"""Feature-redundancy sensitivity: full 10-feature bank vs the bank with IEMG removed.

IEMG = N * MAV exactly for fixed-length windows (N = 512 samples at 250 ms / 2048 Hz), so the two
columns carry identical information. This checks, over all 43 LOSO folds, whether the duplicate
column changes (a) Macro-F1 and (b) the channel-level attribution a model trained on it produces.

Replaces scripts/audit_feature_redundancy.py, which ran 3 participants only; its output
(results/feature_sensitivity.csv) must not be cited as a 43-participant result.

Protocol: the P4 comparison configuration (50 trees, the same stratified 150k outer-training
subsample, seed 20260728), applied identically to both feature sets. Exploratory.

Outputs: artifacts/sensitivity/feature_redundancy.csv, feature_redundancy_summary.csv
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedShuffleSplit
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics  # noqa: E402

CACHE = ROOT / "data" / "cache"
OUT = ROOT / "artifacts" / "sensitivity"
SEED = 20260728
N_CH, N_FPC = 16, 10
CMP_XGB = dict(n_estimators=50, max_depth=6, learning_rate=0.1, subsample=0.8,
               colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)
TRAIN_N = 150000
ATTRIB_N = 5000


def channel_importance(model, Xs, n_fpc):
    contrib = model.get_booster().predict(xgb.DMatrix(Xs), pred_contribs=True)
    phi = np.abs(contrib[:, :, :-1]).mean(axis=1)            # (n, features), drop bias
    return phi.reshape(len(Xs), N_CH, n_fpc).sum(axis=2).mean(axis=0)


def main():
    X = np.load(CACHE / "loso_X.npy", mmap_mode="r")
    y = np.asarray(np.load(CACHE / "loso_y.npy", mmap_mode="r"))
    subj = np.asarray(np.load(CACHE / "loso_subj.npy", mmap_mode="r"))
    fcols = json.loads((CACHE / "loso_features.json").read_text())
    keep9 = np.array([i for i, n in enumerate(fcols) if not n.endswith("_IEMG")])
    assert len(keep9) == N_CH * (N_FPC - 1), len(keep9)
    OUT.mkdir(parents=True, exist_ok=True)

    rows, t0 = [], time.time()
    pids = sorted(np.unique(subj).tolist())
    for i, pid in enumerate(pids, 1):
        te = subj == pid
        Xtr, ytr = np.asarray(X[~te], np.float32), y[~te]
        Xte, yte = np.asarray(X[te], np.float32), y[te]
        sss = StratifiedShuffleSplit(n_splits=1, train_size=TRAIN_N, random_state=SEED)
        idx = next(sss.split(np.zeros((len(ytr), 1)), ytr))[0]
        Xtr, ytr = Xtr[idx], ytr[idx]
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-8
        a, b = (Xtr - mu) / sd, (Xte - mu) / sd
        att_idx = np.random.default_rng(SEED).choice(len(a), ATTRIB_N, replace=False)
        res = {}
        for tag, cols, fpc in (("10feat", np.arange(a.shape[1]), N_FPC), ("9feat", keep9, N_FPC - 1)):
            m = xgb.XGBClassifier(device="cuda", **CMP_XGB)
            m.fit(a[:, cols], ytr)
            res[tag] = (f1_score(yte, m.predict(b[:, cols]), average="macro"),
                        channel_importance(m, a[att_idx][:, cols], fpc))
        rho = spearmanr(res["10feat"][1], res["9feat"][1]).statistic
        top = lambda v, k: set(np.argsort(-v)[:k])
        rows.append({"participant_id": int(pid), "f1_10feat": res["10feat"][0],
                     "f1_9feat_no_iemg": res["9feat"][0],
                     "diff_9_minus_10": res["9feat"][0] - res["10feat"][0],
                     "channel_rank_spearman": float(rho),
                     "top12_identical": top(res["10feat"][1], 12) == top(res["9feat"][1], 12)})
        print(f"[{i}/43] {pid}: diff={rows[-1]['diff_9_minus_10']:+.4f} rho={rho:.3f} "
              f"elapsed={(time.time()-t0)/60:.1f}m", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "feature_redundancy.csv", index=False)
    mean, lcb, ucb = bootstrap_participant_metrics(df.diff_9_minus_10.to_numpy())
    W, p = wilcoxon(df.diff_9_minus_10)
    summ = pd.DataFrame([{"n": len(df), "mean_f1_10feat": df.f1_10feat.mean(),
                          "mean_f1_9feat": df.f1_9feat_no_iemg.mean(), "mean_diff": mean,
                          "sd_diff": df.diff_9_minus_10.std(), "lcb95": lcb, "ucb95": ucb,
                          "wilcoxon_W": W, "p_raw": p,
                          "median_rank_spearman": df.channel_rank_spearman.median(),
                          "n_top12_identical": int(df.top12_identical.sum()),
                          "note": "exploratory; P4 comparison protocol (50 trees, 150k)"}])
    summ.to_csv(OUT / "feature_redundancy_summary.csv", index=False)
    print(summ.T.to_string())
    return 0 if len(df) == 43 else 1


if __name__ == "__main__":
    sys.exit(main())
