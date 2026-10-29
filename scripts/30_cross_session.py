"""Cross-session generalisation: does a model trained on one day work on another?

GRABMyo's three sessions are separated by at least seven days, with the electrode array removed
and reapplied between them. That donning/doffing is the dominant source of real-world degradation
in myoelectric control, and it is the condition a fixed sparse electrode layout has to survive.

Two designs, both keeping the outer participant fully held out:

  CS1  train on session 1 only (of the 42 training participants)
       test the held-out participant separately on sessions 1, 2 and 3
       -> isolates day-to-day degradation for an unseen user

  CS2  train on sessions 1+2, test the held-out participant on session 3
       -> asks whether exposure to more than one day helps

Note on terminology: this measures **cross-session stability**, not "test-retest reliability".
The latter is a measurement-theoretic term implying a reliability coefficient on a stable trait,
which this design does not estimate.

Outputs:
  artifacts/cross_session/cross_session_metrics.csv
  artifacts/cross_session/cross_session_summary.csv
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
import xgboost as xgb

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
OUT = ROOT / "artifacts" / "cross_session"

SEED = 20260728
XGB_PARAMS = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", random_state=SEED, verbosity=0)


def evaluate(model, X, y, mu, sd):
    if len(y) == 0:
        return None
    yp = model.predict((X - mu) / sd)
    return {
        "macro_f1": f1_score(y, yp, average="macro"),
        "balanced_accuracy": balanced_accuracy_score(y, yp),
        "accuracy": accuracy_score(y, yp),
        "weighted_f1": f1_score(y, yp, average="weighted"),
        "n_test_windows": int(len(y)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--resume", action="store_true",
                    help="reuse complete participant/design blocks in the existing output")
    args = ap.parse_args()

    for p in ("loso_X.npy", "loso_y.npy", "loso_subj.npy", "loso_sess.npy"):
        if not (CACHE / p).exists():
            print(f"FATAL: {CACHE/p} missing — run scripts/24 first")
            return 2

    X = np.load(CACHE / "loso_X.npy", mmap_mode="r")
    y = np.asarray(np.load(CACHE / "loso_y.npy", mmap_mode="r"))
    subj = np.asarray(np.load(CACHE / "loso_subj.npy", mmap_mode="r"))
    sess = np.asarray(np.load(CACHE / "loso_sess.npy", mmap_mode="r"))
    participants = sorted(np.unique(subj).tolist())
    print(f"participants={len(participants)} sessions={sorted(np.unique(sess).tolist())}",
          flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    result_path = OUT / "cross_session_metrics.csv"
    rows = []
    completed = set()
    if args.resume and result_path.exists():
        previous = pd.read_csv(result_path)
        expected = {"CS1": {1, 2, 3}, "CS2": {3}}
        for (pid, design), g in previous.groupby(["participant_id", "design"]):
            if set(g.test_session.astype(int)) == expected.get(design, set()):
                completed.add((int(pid), str(design)))
        rows = [r for r in previous.to_dict("records")
                if (int(r["participant_id"]), str(r["design"])) in completed]
        print(f"resuming {len(completed)} complete participant/design blocks", flush=True)
    t0 = time.time()

    for i, pid in enumerate(participants, 1):
        is_test = subj == pid
        is_train_subj = ~is_test

        for design, train_sessions, test_sessions in (
            ("CS1", (1,), (1, 2, 3)),
            ("CS2", (1, 2), (3,)),
        ):
            if (int(pid), design) in completed:
                continue
            tr = is_train_subj & np.isin(sess, train_sessions)
            Xtr = np.asarray(X[tr], dtype=np.float32)
            ytr = y[tr]
            mu = Xtr.mean(axis=0)
            sd = Xtr.std(axis=0) + 1e-8

            model = xgb.XGBClassifier(device=args.device, **XGB_PARAMS)
            model.fit((Xtr - mu) / sd, ytr)

            for ts in test_sessions:
                te = is_test & (sess == ts)
                res = evaluate(model, np.asarray(X[te], dtype=np.float32), y[te], mu, sd)
                if res is None:
                    continue
                rows.append({
                    "participant_id": int(pid), "design": design,
                    "train_sessions": "+".join(map(str, train_sessions)),
                    "test_session": int(ts), "n_train_windows": int(tr.sum()),
                    "matched_session": bool(ts in train_sessions), **res,
                })

        pd.DataFrame(rows).to_csv(result_path, index=False)
        el = time.time() - t0
        print(f"[{i}/{len(participants)}] participant {pid:02d} "
              f"elapsed={el/60:.1f}m eta={el/i*(len(participants)-i)/60:.1f}m", flush=True)

    df = pd.DataFrame(rows)
    summary = (df.groupby(["design", "train_sessions", "test_session", "matched_session"])
               .agg(n_participants=("participant_id", "nunique"),
                    mean_macro_f1=("macro_f1", "mean"),
                    sd_macro_f1=("macro_f1", "std"),
                    mean_accuracy=("accuracy", "mean"))
               .reset_index())
    summary.to_csv(OUT / "cross_session_summary.csv", index=False)
    print("\n" + summary.to_string(index=False), flush=True)

    # Degradation from the trained-on day to unseen days, paired within participant
    cs1 = df[df.design == "CS1"]
    base = cs1[cs1.test_session == 1].set_index("participant_id").macro_f1
    for ts in (2, 3):
        other = cs1[cs1.test_session == ts].set_index("participant_id").macro_f1
        common = base.index.intersection(other.index)
        d = (other.loc[common] - base.loc[common])
        print(f"CS1 session 1 -> session {ts}: mean change {d.mean():+.4f} "
              f"(sd {d.std():.4f}, n={len(common)})", flush=True)

    if df.participant_id.nunique() != len(participants):
        print("ASSERTION FAILED: not every participant covered")
        return 1
    print(f"\nASSERTION PASSED: {len(participants)} participants")
    print(f"wall clock: {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
