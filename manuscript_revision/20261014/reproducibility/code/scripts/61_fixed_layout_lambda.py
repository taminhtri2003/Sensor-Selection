"""Fixed-layout consistency check with the primary ranking (decision log 24a).

The original check (scripts/audit_fixed_population_layout.py) derived one 12-electrode layout on
the odd-numbered participants with lambda = 0.5 and tested it on the even-numbered participants.
The primary analysis ranks with lambda = 0, and no rationale for 0.5 was recorded. This script
repeats the check with exactly the same data split, attribution settings, seed and XGBoost
configuration, derives the layout for every lambda candidate from ONE attribution run, and also
runs the swapped split (development = even, test = odd).

Leakage contract: the attribution, the scaler and both models see development participants only.
Test participants are used only for prediction.

Outputs (isolated; the original artifacts are not touched):
  artifacts/completion_analyses/fixed_layout/per_participant.csv
  artifacts/completion_analyses/fixed_layout/summary.csv
  artifacts/completion_analyses/fixed_layout/summary.json
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics  # noqa: E402
from src.semg_sparse.xai.cross_fitted import compute_cross_fitted_attribution  # noqa: E402

SEED = 20260728
N_CHANNELS = 16
N_FPC = 10
K = 12
MARGIN = 0.02
LAMBDAS = (0.0, 0.25, 0.5, 1.0)
ORIGINAL_DROPPED_LAM05 = {3, 9, 11, 12}   # artifacts/fixed_layout/fixed_layout_summary.json
XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", device="cuda",
                  random_state=SEED, verbosity=0)
OUT = ROOT / "artifacts" / "completion_analyses" / "fixed_layout"


def channel_columns(channels_1based):
    cols = []
    for c in channels_1based:
        cols.extend(range((c - 1) * N_FPC, (c - 1) * N_FPC + N_FPC))
    return np.array(sorted(cols), dtype=np.int64)


def run_split(name, dev_pids, test_pids, X, y, subj, fcols):
    dev_mask = np.isin(subj, dev_pids)
    X_dev = np.asarray(X[dev_mask], dtype=np.float32)
    y_dev = np.asarray(y[dev_mask])
    s_dev = np.asarray(subj[dev_mask])
    if set(np.unique(s_dev).tolist()) & set(test_pids.tolist()):
        raise AssertionError("test participant in development data")

    # Same call as the original audit script (max_train_samples=None, 20k attributed windows).
    res = compute_cross_fitted_attribution(
        X_dev, y_dev, s_dev, fcols, n_channels=N_CHANNELS, n_features_per_channel=N_FPC,
        n_inner_folds=5, device="cuda", max_attrib_samples=20000, max_train_samples=None,
        seed=SEED, excluded_subjects=tuple(int(p) for p in test_pids),
    )
    rankings = {lam: [int(c) + 1 for c in res.ranking(lam=lam)] for lam in LAMBDAS}

    mu = X_dev.mean(axis=0)
    sd = X_dev.std(axis=0) + 1e-8
    Xd = (X_dev - mu) / sd
    m16 = xgb.XGBClassifier(**XGB_PARAMS)
    m16.fit(Xd, y_dev)

    models12 = {}
    for lam in LAMBDAS:
        key = tuple(sorted(rankings[lam][:K]))
        if key not in models12:
            m = xgb.XGBClassifier(**XGB_PARAMS)
            m.fit(Xd[:, channel_columns(key)], y_dev)
            models12[key] = m

    rows = []
    for pid in test_pids:
        mask = subj == pid
        Xp = (np.asarray(X[mask], dtype=np.float32) - mu) / sd
        yp = np.asarray(y[mask])
        f16 = f1_score(yp, m16.predict(Xp), average="macro")
        f12 = {key: f1_score(yp, m.predict(Xp[:, channel_columns(key)]), average="macro")
               for key, m in models12.items()}
        for lam in LAMBDAS:
            key = tuple(sorted(rankings[lam][:K]))
            rows.append({"split": name, "lambda": lam, "test_participant": int(pid),
                         "layout": ";".join(map(str, key)),
                         "macro_f1_full16": f16, "macro_f1_fixed12": f12[key],
                         "diff_12_minus_16": f12[key] - f16})

    per = pd.DataFrame(rows)
    summary = []
    for lam in LAMBDAS:
        g = per[per["lambda"] == lam].sort_values("test_participant")
        mean, lcb, ucb = bootstrap_participant_metrics(g.diff_12_minus_16.to_numpy(),
                                                       n_resamples=10000, seed=SEED)
        dropped = sorted(set(range(1, N_CHANNELS + 1)) - set(rankings[lam][:K]))
        summary.append({
            "split": name, "lambda": lam, "n_dev": int(len(dev_pids)),
            "n_test": int(len(test_pids)), "ranking": ";".join(map(str, rankings[lam])),
            "dropped": ";".join(map(str, dropped)),
            "mean_full16": float(g.macro_f1_full16.mean()),
            "mean_fixed12": float(g.macro_f1_fixed12.mean()),
            "mean_diff": mean, "lcb95": lcb, "ucb95": ucb,
            "non_inferior_002": bool(lcb > -MARGIN),
        })
    return per, pd.DataFrame(summary)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = ROOT / "data" / "cache"
    X = np.load(cache / "loso_X.npy", mmap_mode="r")
    y = np.load(cache / "loso_y.npy", mmap_mode="r")
    subj = np.asarray(np.load(cache / "loso_subj.npy", mmap_mode="r"))
    fcols = json.loads((cache / "loso_features.json").read_text())

    odd = np.array([p for p in range(1, 44) if p % 2 == 1])
    even = np.array([p for p in range(1, 44) if p % 2 == 0])
    pers, sums = [], []
    for name, dev, test in (("dev_odd_test_even", odd, even), ("dev_even_test_odd", even, odd)):
        print(f"split {name}: dev={len(dev)} test={len(test)}", flush=True)
        per, summ = run_split(name, dev, test, X, y, subj, fcols)
        print(summ[["lambda", "dropped", "mean_diff", "lcb95", "ucb95",
                    "non_inferior_002"]].to_string(index=False), flush=True)
        pers.append(per)
        sums.append(summ)

    per = pd.concat(pers, ignore_index=True)
    summ = pd.concat(sums, ignore_index=True)
    orig = summ[(summ.split == "dev_odd_test_even") & (summ["lambda"] == 0.5)].iloc[0]
    reproduced = set(map(int, orig.dropped.split(";"))) == ORIGINAL_DROPPED_LAM05
    per.to_csv(OUT / "per_participant.csv", index=False)
    summ.to_csv(OUT / "summary.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps({
        "decision_log": "Decision 24a",
        "original_lambda05_dropped_reproduced": bool(reproduced),
        "margin": MARGIN, "k": K, "seed": SEED,
    }, indent=2))
    print(f"original lambda=0.5 dropped set reproduced: {reproduced}")
    return 0 if reproduced else 1


if __name__ == "__main__":
    sys.exit(main())
