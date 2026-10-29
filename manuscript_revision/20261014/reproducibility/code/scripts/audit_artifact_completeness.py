"""Audit completeness of every result artifact before it is used in the manuscript."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "artifacts"
rows = []

def check(name, path, pid_col, expect_n, extra=None):
    p = A / path
    if not p.exists():
        rows.append((name, path, "MISSING", "")); return None
    df = pd.read_csv(p)
    n = df[pid_col].nunique()
    status = "OK" if n == expect_n else "INCOMPLETE"
    info = f"rows={len(df)} participants={n}/{expect_n}"
    if extra:
        s, msg = extra(df)
        info += "; " + msg
        if not s: status = "FAIL"
    if df.select_dtypes("number").isna().any().any():
        info += "; NaN present in numeric cols"
    rows.append((name, path, status, info))
    return df

def grid(cols):
    def f(df):
        g = df.groupby(cols).size()
        return g.nunique() == 1, f"cells={len(g)} each_n={sorted(g.unique().tolist())}"
    return f

check("P1 XGB", "metrics/loso_full_channel_subject_metrics_xgb.csv", "participant_id", 43)
check("P1 SVM/RF", "metrics/loso_full_channel_subject_metrics_svmrf.csv", "participant_id", 43, grid(["model"]))
check("P2 scores", "rankings/cross_fitted_scores.csv", "outer_participant", 43, grid(["outer_participant"]))
check("P2 rankings", "rankings/cross_fitted_rankings.csv", "outer_participant", 43)
check("P2 per-subject", "rankings/per_subject_attribution.csv",
      [c for c in pd.read_csv(A/"rankings/per_subject_attribution.csv", nrows=1).columns if "outer" in c][0], 43)
check("P3 curve", "metrics/sparse_curve_subject_metrics.csv", "participant_id", 43, grid(["lambda", "channels_k"]))
check("P4 baselines", "selection_baselines/selection_baseline_metrics.csv", "participant_id", 43, grid(["method", "channels_k"]))
check("P7 cross-session", "cross_session/cross_session_metrics.csv", "participant_id", 43, grid(["design", "test_session"]))
fp = A / "faithfulness/deletion_curves.csv"
d = pd.read_csv(fp); pcol = "participant_id" if "participant_id" in d else d.columns[0]
check("P8 faithfulness", "faithfulness/deletion_curves.csv", pcol, 43, grid(["arm", "n_kept"]))
check("P9 DB5 full", "db5/db5_full_channel_metrics.csv", "participant_id", 10)
check("P9 DB5 curve", "db5/db5_sparse_curve.csv", "participant_id", 10, grid(["channels_k"]))
check("P9 DB5 rankings", "db5/db5_rankings.csv", "outer_participant", 10)

out = pd.DataFrame(rows, columns=["artifact", "path", "status", "detail"])
print(out.to_string(index=False))
out.to_csv(ROOT / "reports" / "artifact_completeness_audit.csv", index=False)
sys.exit(0 if (out.status == "OK").all() else 1)
