"""Independent numerical audit for the pre-submission review.

Recomputes every decision-relevant quantity from per-participant result files (not from the
statistics CSVs the macros read), prints unrounded values, and compares them with the macro
values in the manuscript. Also computes the Holm-adjusted H1 family, which the frozen plan
requires (multiplicity: Holm, applied to each confirmatory family H1-H4) but scripts/28 did not
apply to the non-inferiority tests.

Output: reports/presubmission_numeric_audit.csv (+ stdout)
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics as boot  # noqa: E402

A = ROOT / "artifacts"
macros = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}",
                         (ROOT / "manuscript/generated/results_macros.tex").read_text(encoding="utf-8")))
rows = []


def rec(item, value, macro=None, fmt="{:+.4f}", note=""):
    shown = macros.get(macro) if macro else None
    ok = None
    if macro:
        try:
            ok = abs(float(shown.replace("{,}", "").replace("< ", "").replace("= ", "")) - float(value)) \
                <= 0.5 * 10 ** -(len(shown.split(".")[-1]) if "." in shown else 0) + 1e-12
        except ValueError:
            ok = str(shown).strip() == str(value)
    rows.append({"item": item, "unrounded": value, "macro": macro, "manuscript": shown,
                 "consistent": ok, "note": note})


def one_sided_p(d, margin, seed=20260728, n=10000):
    """bootstrap p for H0: mean(d) <= -margin (share of resampled means at or below -margin)"""
    rng = np.random.default_rng(seed)
    b = d[rng.integers(0, len(d), (n, len(d)))].mean(1)
    return max((b <= -margin).mean(), 1 / n)


def holm(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    adj = np.empty(len(p))
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(1, run)
    return adj


# ---------- P1
x = pd.read_csv(A / "metrics/loso_full_channel_subject_metrics_xgb.csv").set_index("participant_id").macro_f1
s = pd.read_csv(A / "metrics/loso_full_channel_subject_metrics_svmrf.csv")
sv = s[s.model == "M_SVM"].set_index("participant_id").macro_f1
m, l, u = boot(x.to_numpy())
rec("P1 XGB mean", m, "FullXGB", note=f"n={len(x)}")
rec("P1 XGB LCB", l, "FullXGBLCB")
d = (x - sv.loc[x.index]).to_numpy()
rec("P1 XGB-SVM diff", d.mean(), "XGBvsSVMDiff")

# ---------- H1 (lambda = 0, per participant, reference = k16 of same curve)
c = pd.read_csv(A / "metrics/sparse_curve_subject_metrics.csv")
for lam in (0.0, 0.25, 0.5, 1.0):
    w = c[np.isclose(c["lambda"], lam)].pivot(index="participant_id", columns="channels_k", values="macro_f1")
    assert w.shape == (43, 16)
    res = {}
    for mg in (0.01, 0.02, 0.03):
        lcbs = {k: boot((w[k] - w[16]).to_numpy())[1] for k in range(1, 16)}
        ks = [k for k, v in lcbs.items() if v > -mg]
        kstar = min(ks) if ks else None
        ps = [one_sided_p((w[k] - w[16]).to_numpy(), mg) for k in range(1, 16)]
        padj = holm(ps)
        ks_h = [k for k, p in zip(range(1, 16), padj) if p < 0.025]
        # fixed-sequence from k = 15 downward at one-sided alpha 0.025
        fs = None
        for k in range(15, 0, -1):
            if lcbs[k] > -mg:
                fs = k
            else:
                break
        res[mg] = (kstar, min(ks_h) if ks_h else None, fs, lcbs)
        if lam == 0.0:
            rec(f"H1 lambda=0 margin={mg} k* (plan rule)", kstar,
                {0.01: "KStarMarginPtOne", 0.02: "KStar", 0.03: "KStarMarginPtThree"}[mg], fmt="{}")
            rec(f"H1 lambda=0 margin={mg} k* with Holm over 15 k (one-sided bootstrap p<0.025)",
                min(ks_h) if ks_h else "none", note="plan requires Holm within H1; not applied by scripts/28")
            rec(f"H1 lambda=0 margin={mg} k* fixed-sequence (post hoc)", fs if fs else "none")
    if lam == 0.0:
        L = res[0.02][3]
        for k in (11, 12, 13):
            rec(f"H1 lambda=0 k={k} LCB (unrounded)", L[k],
                {11: "DeltaKElevenLCB", 12: "DeltaKTwelveLCB", 13: None}[k])
        rec("H1 lambda=0 k=12 mean delta", (w[12] - w[16]).mean(), "DeltaKTwelve")
        rec("H1 lambda=0 k=12 n", int(w[12].notna().sum()))
    else:
        rec(f"H1 lambda={lam} k* at 0.01/0.02/0.03", "/".join(str(res[mg][0]) for mg in (0.01, 0.02, 0.03)))

# ---------- H4 ordering (per-participant arms)
f = pd.read_csv(A / "faithfulness/deletion_curves.csv")
g = f.groupby(["n_kept", "arm"]).macro_f1.mean().unstack()
for k, r in g.iterrows():
    arms = [a for a in ("remove_top", "remove_random", "remove_bottom") if pd.notna(r.get(a))]
    order = all(r[arms[i]] < r[arms[i + 1]] for i in range(len(arms) - 1))
    rec(f"H4 n_kept={k} ordering top<random<bottom", "holds" if order else "VIOLATED",
        note="; ".join(f"{a}={r[a]:.4f}" for a in arms))

# ---------- bipolar
b = pd.read_csv(A / "bipolar/bipolar_sparse_curve.csv")
w = b[np.isclose(b["lambda"], 0.0)].pivot(index="participant_id", columns="channels_k", values="macro_f1")
for k in (6, 7):
    mm, ll, uu = boot((w[k] - w[8]).to_numpy())
    rec(f"Bipolar k={k} delta vs k=8 (unrounded)", mm, {6: "BipDeltaKSix", 7: "BipDeltaKSeven"}[k])
    rec(f"Bipolar k={k} LCB (unrounded)", ll, {6: "BipDeltaKSixLCB", 7: "BipDeltaKSevenLCB"}[k],
        note="decision uses LCB > -0.02, not raw mean F1")
rec("Bipolar raw mean F1 k=7 minus k=8 (NOT the decision quantity)", w[7].mean() - w[8].mean())

# ---------- DB5
db = pd.read_csv(A / "db5/db5_sparse_curve.csv")
w = db.pivot(index="participant_id", columns="channels_k", values="macro_f1")
for k in (12, 13):
    mm, ll, uu = boot((w[k] - w[16]).to_numpy())
    rec(f"DB5 k={k} LCB (unrounded, 6 dp)", round(ll, 6),
        {12: "DBFiveDeltaKTwelveLCB", 13: "DBFiveDeltaKThirteenLCB"}[k], note=f"n={len(w)}; > -0.02 ? {ll > -0.02}")
mono = all(w.mean()[k] <= w.mean()[k + 1] for k in range(1, 16))
rec("DB5 mean curve monotone non-decreasing in k", mono, note="Results text says 'same monotone shape'")

out = pd.DataFrame(rows)
out.to_csv(ROOT / "reports/presubmission_numeric_audit.csv", index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 70)
print(out.to_string(index=False))
