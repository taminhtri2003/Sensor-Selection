"""Statistics for the completion analyses (decision log 24).

For each condition (17-class task, 150 ms and 500 ms windows) the non-inferiority analysis of
the primary H1 is repeated exactly: paired participant differences against k = 16 of the same
condition, 10,000-resample participant cluster bootstrap, k* = min{k < 16 : LCB95 > -delta} at
delta = 0.01, 0.02, 0.03, Holm and the post-hoc fixed sequence as in supplementary table S3.
The code path is scripts/37_secondary_statistics.holm_ni, the one used for the primary H1.

Outputs: artifacts/completion_analyses/
  completion_non_inferiority_by_k.csv   one row per condition x margin x k
  completion_kstar.csv                  k* per condition and margin
  completion_full_array.csv             k = 16 and k = 12 Macro-F1 per condition with 95% CI
"""

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics  # noqa: E402

m37 = importlib.import_module("37_secondary_statistics")
OUT = ROOT / "artifacts" / "completion_analyses"
CONDITIONS = {
    "primary_250ms": ROOT / "artifacts" / "metrics" / "sparse_curve_subject_metrics.csv",
    "rest17": OUT / "rest17" / "sparse_curve_subject_metrics.csv",
    "w150": OUT / "w150" / "sparse_curve_subject_metrics.csv",
    "w500": OUT / "w500" / "sparse_curve_subject_metrics.csv",
}
N_PARTICIPANTS = 43
KS = list(range(1, 17))


def load(cond, path):
    c = pd.read_csv(path)
    c = c[np.isclose(c["lambda"], 0.0)]
    grid = c.groupby("channels_k").participant_id.nunique()
    if sorted(grid.index) != KS or (grid != N_PARTICIPANTS).any():
        raise SystemExit(f"FATAL: incomplete grid for {cond}: {grid.to_dict()}")
    if c.duplicated(["participant_id", "channels_k"]).any():
        raise SystemExit(f"FATAL: duplicate rows for {cond}")
    if not np.isfinite(c.macro_f1).all():
        raise SystemExit(f"FATAL: nonfinite scores for {cond}")
    return c


def main():
    ni, kstar, full = [], [], []
    ref = None
    for cond, path in CONDITIONS.items():
        if not path.exists():
            raise SystemExit(f"FATAL: {path} missing")
        c = load(cond, path)
        if cond != "primary_250ms":
            # Selected electrodes must be the primary lambda = 0 rankings (decision 24b/c).
            prim = load("primary_250ms", CONDITIONS["primary_250ms"])
            a = c.set_index(["participant_id", "channels_k"]).channels.sort_index()
            b = prim.set_index(["participant_id", "channels_k"]).channels.sort_index()
            if not a.equals(b):
                raise SystemExit(f"FATAL: {cond} did not use the primary electrode subsets")
        df = m37.holm_ni(c, 16, cond, lam=0.0)
        df["condition"] = cond
        ni.append(df)
        for m, g in df.groupby("margin"):
            kstar.append({"condition": cond, "margin": m,
                          "kstar_unadjusted": g.k[g.ni_unadjusted].min(),
                          "kstar_holm": g.k[g.ni_holm].min(),
                          "kstar_fixed_sequence": g.k[g.ni_fixed_sequence_posthoc].min(),
                          "all_k_ge_kstar_noninferior": bool(
                              g.ni_unadjusted[g.k >= g.k[g.ni_unadjusted].min()].all())
                          if g.ni_unadjusted.any() else False})
        s16 = m37.series(c, channels_k=16).sort_index()
        if ref is None:
            ref = s16
        for k in (16, 12):
            s = m37.series(c, channels_k=k).sort_index()
            mean, lcb, ucb = bootstrap_participant_metrics(s.to_numpy(), n_resamples=10000)
            row = {"condition": cond, "k": k, "mean_macro_f1": mean, "lcb95": lcb, "ucb95": ucb}
            if k == 16 and cond not in ("primary_250ms", "rest17"):
                # descriptive: full-array change relative to 250 ms, same participants
                d = (s - ref.loc[s.index]).to_numpy()
                dm, dl, du = bootstrap_participant_metrics(d, n_resamples=10000)
                row.update(diff_vs_250ms=dm, diff_lcb95=dl, diff_ucb95=du)
            full.append(row)
    pd.concat(ni, ignore_index=True).to_csv(OUT / "completion_non_inferiority_by_k.csv",
                                            index=False)
    ks = pd.DataFrame(kstar)
    ks.to_csv(OUT / "completion_kstar.csv", index=False)
    pd.DataFrame(full).to_csv(OUT / "completion_full_array.csv", index=False)
    print(ks.to_string(index=False))
    print(pd.DataFrame(full).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
