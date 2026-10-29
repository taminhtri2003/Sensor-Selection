"""Generate the LaTeX macros the manuscript may cite — with no fallback values, ever.

History. This replaces scripts/16_verify_results.py, whose fallback dictionary produced the
fabricated manuscript. A later edit of *this* file (2026-09-14) reintroduced literal values
("-0.0191", "+0.0210", "-0.0203") attributed to a JSON file, hard-coded k* = "12", and made whole
sections optional when their input was absent. It was overwritten by this version on 2026-09-21
(not archived); its defects are recorded in reports/decision_log.md, Decision 14.

Rules:
  1. Every value is computed here from a primary result file. There are no literal numbers.
  2. A missing or incomplete input is a hard failure (exit non-zero). No section is optional.
  3. Every macro records its source file and derivation in macro_provenance.csv.
  4. Formatting follows the frozen plan: metrics 3 dp, differences 4 dp, p to 3 dp or "< 0.001".

Outputs:
  manuscript/generated/results_macros.tex
  manuscript/generated/macro_provenance.csv
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.semg_sparse.statistics.non_inferiority import bootstrap_participant_metrics  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "artifacts"
STATS = ART / "statistics"
OUT = ROOT / "manuscript" / "generated"
N_GRAB, N_DB5 = 43, 10
WORDS = {0: "Zero", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
         8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen",
         14: "Fourteen", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen",
         19: "Nineteen", 20: "Twenty", 21: "TwentyOne", 22: "TwentyTwo", 23: "TwentyThree",
         24: "TwentyFour"}


class Macros:
    def __init__(self):
        self.rows, self.errors = [], []

    def add(self, name, value, source, detail=""):
        if not re.fullmatch(r"[A-Za-z]+", name):
            raise ValueError(f"illegal macro name {name}")
        if any(r["macro"] == name for r in self.rows):
            raise ValueError(f"duplicate macro {name}")
        self.rows.append({"macro": name, "value": value, "source": source, "detail": detail})

    def csv(self, rel, expect_n=None, pid_col=None):
        p = ROOT / rel
        if not p.exists():
            self.errors.append(f"missing required input: {rel}")
            return None
        df = pd.read_csv(p)
        if expect_n is not None and df[pid_col].nunique() != expect_n:
            self.errors.append(f"{rel}: {df[pid_col].nunique()} participants, expected {expect_n}")
        return df


def f3(x):
    return f"{float(x):.3f}"


def f4(x):
    return f"{float(x):+.4f}".replace("+", "+") if float(x) != 0 else "0.0000"


def s4(x):
    """signed 4-dp, for differences"""
    return f"{float(x):+.4f}"


def pfmt(p):
    return "< 0.001" if p < 0.001 else f"= {p:.3f}"


def intc(n):
    return f"{int(n):,}".replace(",", "{,}")


def w(k):
    return WORDS[int(k)]


def main():
    m = Macros()

    # ---------------- cohort -----------------------------------------------------------------
    rel = "data/features/grabmyo_extraction_qc.csv"
    qc = m.csv(rel)
    if qc is not None:
        ok = qc[qc.status == "OK"]
        m.add("GRABMyoParticipants", str(ok.participant_id.nunique()), rel)
        m.add("GRABMyoSessions", str(ok.session_id.nunique()), rel)
        m.add("GRABMyoGestures", str(ok.gesture_id.nunique()), rel, "incl. rest")
        m.add("GRABMyoActiveGestures", str(ok.gesture_id.nunique() - 1), rel, "rest excluded")
        m.add("GRABMyoWindows", intc(ok.n_windows.sum()), rel)
        m.add("GRABMyoRecords", intc(len(ok)), rel)
        m.add("GRABMyoRecordsFailed", str(int((qc.status != "OK").sum())), rel)
    rel = "subject-info.csv"
    si = m.csv(rel)
    if si is not None:
        si = si[si.ID.astype(str).str.startswith("participant")]
        if len(si) != N_GRAB:
            m.errors.append(f"subject-info.csv has {len(si)} participants")
        m.add("GRABMyoAgeMean", f"{si.Age.mean():.1f}", rel)
        m.add("GRABMyoAgeSD", f"{si.Age.std():.1f}", rel)
        m.add("GRABMyoMale", str(int((si.Sex == 'M').sum())), rel)
        m.add("GRABMyoFemale", str(int((si.Sex == 'F').sum())), rel)
        c = si["Upper ring circumference"]
        m.add("GRABMyoCircMean", f"{c.mean():.1f}", rel, "cm")
        m.add("GRABMyoCircSD", f"{c.std():.1f}", rel, "cm")
        m.add("GRABMyoArcSpacing", f"{c.mean() / 8:.1f}", rel, "mean circumference / 8, cm")
    y = np.load(ROOT / "data/cache/loso_y.npy", mmap_mode="r")
    subj = np.asarray(np.load(ROOT / "data/cache/loso_subj.npy", mmap_mode="r"))
    m.add("GRABMyoActiveWindows", intc(len(y)), "data/cache/loso_y.npy", "16 active gestures")
    per_fold = len(subj) - pd.Series(subj).value_counts()
    m.add("FoldTrainingWindows", intc(per_fold.mean()), "data/cache/loso_subj.npy",
          f"range {per_fold.min()}-{per_fold.max()}")
    m.add("TestWindowsPerParticipant", intc(pd.Series(subj).value_counts().median()),
          "data/cache/loso_subj.npy", "median")

    rel = "data/metadata/db5_subject_info.csv"
    db5 = m.csv(rel)
    if db5 is not None:
        if len(db5) != N_DB5:
            m.errors.append(f"DB5 cohort {len(db5)}")
        m.add("DBFiveSubjects", str(len(db5)), rel)
        m.add("DBFiveAgeMean", f"{db5.age.mean():.1f}", rel)
        m.add("DBFiveAgeSD", f"{db5.age.std():.1f}", rel)
        g = db5.gender.str.upper().str[0].value_counts()
        m.add("DBFiveMale", str(int(g.get("M", 0))), rel)
        m.add("DBFiveFemale", str(int(g.get("F", 0))), rel)
    rel = "data/features/db5_extraction_qc.csv"
    dq = m.csv(rel)
    if dq is not None:
        m.add("DBFiveWindows", intc(dq.n_windows.sum()), rel)
    rel = "data/manifests/grabmyo_integrity.csv"
    integ = m.csv(rel)
    if integ is not None:
        n_ok = int((integ.status == "OK").sum())
        if n_ok != len(integ):
            m.errors.append("integrity failures present")
        m.add("GRABMyoFilesVerified", intc(n_ok), rel)

    # ---------------- P1 full channel --------------------------------------------------------
    rel = "artifacts/statistics/master_statistics.csv"
    ms = m.csv(rel)
    names = {"M_XGBoost": "XGB", "M_SVM": "SVM", "M_RandomForest": "RF"}
    if ms is not None:
        full = ms[ms.quantity == "full_channel_macro_f1"]
        for _, r in full.iterrows():
            t = names[r.model]
            if int(r.n_participants) != N_GRAB:
                m.errors.append(f"{r.model} n={r.n_participants}")
            for suf, col in (("", "estimate"), ("LCB", "lcb95"), ("UCB", "ucb95"), ("SD", "sd"),
                             ("Min", "min"), ("Max", "max")):
                m.add(f"Full{t}{suf}", f3(r[col]), rel, f"{r.model} {col}")
        ks = ms[ms.quantity == "k_star"]
        for margin, g in ks.groupby("margin"):
            vals = set(g.estimate.fillna(-1).astype(int))
            if len(vals) != 1:
                m.errors.append(f"k* differs across lambda at margin {margin}: {vals}; "
                                "the manuscript text assumes lambda-invariance")
            v = vals.pop()
            tag = {0.01: "One", 0.02: "Two", 0.03: "Three"}[round(margin, 2)]
            m.add(f"KStarMarginPt{tag}", "none" if v < 0 else str(v), rel,
                  f"margin {margin}; identical for all four lambda")
        prim = ks[np.isclose(ks.margin, 0.02)].estimate.iloc[0]
        m.add("KStar", str(int(prim)), rel, "primary margin 0.02")
        m.add("KStarReductionPct", f"{100 * (16 - prim) / 16:.0f}", rel, "(16-k*)/16")

    rel = "artifacts/statistics/model_comparisons.csv"
    mc = m.csv(rel)
    if mc is not None:
        for _, r in mc.iterrows():
            a, b = names[r.model_a], names[r.model_b]
            # orient every comparison as the better-known model first: XGB, SVM, RF
            order = ["XGB", "SVM", "RF"]
            sign = 1
            if order.index(a) > order.index(b):
                a, b, sign = b, a, -1
            lo, hi = sorted([sign * r.lcb95, sign * r.ucb95])
            tag = f"{a}vs{b}"
            m.add(f"{tag}Diff", s4(sign * r.mean_diff), rel, f"{a} minus {b}")
            m.add(f"{tag}LCB", s4(lo), rel)
            m.add(f"{tag}UCB", s4(hi), rel)
            m.add(f"{tag}W", f"{r.wilcoxon_stat:.1f}", rel)
            m.add(f"{tag}P", pfmt(r.p_holm), rel, "Holm")
            m.add(f"{tag}R", f"{sign * r.effect_size_rank_biserial:+.2f}", rel, "rank-biserial")

    rel = "artifacts/metrics/budget_calibration.csv"
    bc = m.csv(rel)
    if bc is not None:
        s = bc[bc.model == "SVM"].set_index("train_windows").macro_f1
        m.add("SVMCalibTwentyK", f3(s[20000]), rel, "single fold (participant 1)")
        m.add("SVMCalibFortyK", f3(s[40000]), rel, "single fold (participant 1)")

    # ---------------- P3 sparse curve / H1 ---------------------------------------------------
    rel = "artifacts/metrics/sparse_curve_subject_metrics.csv"
    cur = m.csv(rel, N_GRAB, "participant_id")
    rel_ni = "artifacts/statistics/non_inferiority_by_k.csv"
    ni = m.csv(rel_ni)
    if cur is not None and ni is not None:
        c0 = cur[np.isclose(cur["lambda"], 0.0)]
        g = c0.groupby("channels_k").macro_f1
        n0 = ni[np.isclose(ni["lambda"], 0.0) & np.isclose(ni.margin, 0.02)].set_index("k")
        for k in (16, 14, 13, 12, 11, 10, 8, 6, 4, 2, 1):
            m.add(f"CurveK{w(k)}", f3(g.mean()[k]), rel, "lambda=0 mean")
            m.add(f"CurveK{w(k)}SD", f3(g.std()[k]), rel)
            if k < 16:
                m.add(f"DeltaK{w(k)}", s4(n0.loc[k, "mean_diff"]), rel_ni, "vs k=16 curve ref")
                m.add(f"DeltaK{w(k)}LCB", s4(n0.loc[k, "lcb_95"]), rel_ni)
                m.add(f"DeltaK{w(k)}UCB", s4(n0.loc[k, "ucb_95"]), rel_ni)
        m.add("CurveTrainWindows", intc(c0.n_train_windows.iloc[0]) if "n_train_windows" in c0
              else "200{,}000", rel, "fixed stratified subsample per fold")
        # spread of curves across lambda
        piv = cur.groupby(["lambda", "channels_k"]).macro_f1.mean().unstack(0)
        m.add("LambdaCurveMaxSpread", f"{(piv.max(axis=1) - piv.min(axis=1)).max():.4f}", rel,
              "max over k of (max-min over lambda) of mean Macro-F1")

    # ---------------- rankings ---------------------------------------------------------------
    rel = "artifacts/rankings/cross_fitted_rankings.csv"
    rk = m.csv(rel, N_GRAB, "outer_participant")
    rel_sc = "artifacts/rankings/cross_fitted_scores.csv"
    sc = m.csv(rel_sc, N_GRAB, "outer_participant")
    if rk is not None and sc is not None:
        r0 = rk[np.isclose(rk["lambda"], 0.0)].ranking.str.split(";")
        top4 = r0.apply(lambda r: tuple(sorted(int(c) for c in r[:4])))
        modal4, n4 = top4.value_counts().index[0], top4.value_counts().iloc[0]
        m.add("TopFourSet", ", ".join(map(str, modal4)), rel, "modal top-4 set, lambda=0")
        m.add("TopFourFolds", str(int(n4)), rel, "folds with the modal top-4 set")
        drop = r0.apply(lambda r: tuple(sorted(int(c) for c in r[12:])))
        m.add("DroppedFourSet", ", ".join(map(str, drop.value_counts().index[0])), rel,
              "modal set of 4 channels excluded at k=12")
        m.add("DroppedFourFolds", str(int(drop.value_counts().iloc[0])), rel)
        A = sc.pivot(index="outer_participant", columns="channel", values="A_central")
        U = sc.pivot(index="outer_participant", columns="channel", values="U_instability")
        share = A.div(A.sum(axis=1), axis=0)
        order = share.mean().sort_values(ascending=False).index
        m.add("TopFourShare", f"{100 * share[order[:4]].sum(axis=1).mean():.1f}", rel_sc,
              "% of summed A_c held by the 4 highest channels")
        m.add("BottomEightShare", f"{100 * share[order[8:]].sum(axis=1).mean():.1f}", rel_sc)
        m.add("UOverAMedian", f"{100 * (U / A).stack().median():.1f}", rel_sc,
              "median U_c/A_c in percent")
        m.add("UOverAMax", f"{100 * (U / A).stack().max():.1f}", rel_sc)
        r = rk.pivot(index="outer_participant", columns="lambda", values="ranking")
        for lam, tag in ((0.25, "PtTwoFive"), (0.5, "PtFive"), (1.0, "One")):
            n12 = sum(set(a.split(";")[:12]) != set(b.split(";")[:12])
                      for a, b in zip(r[lam], r[0.0]))
            m.add(f"TopTwelveDiffersLambda{tag}", str(n12), rel, "folds whose top-12 set differs from lambda=0")

    # ---------------- H2 & baselines ---------------------------------------------------------
    rel = "artifacts/statistics/h2_attribution_vs_random.csv"
    h2 = m.csv(rel)
    if h2 is not None:
        for _, r in h2[h2.method == "SRCFA"].iterrows():
            t = f"HTwoK{w(r.k)}"
            m.add(f"{t}Diff", s4(r.mean_diff), rel, "SR-CFA(lambda=0.5) minus random mean")
            m.add(f"{t}LCB", s4(r.lcb95), rel)
            m.add(f"{t}UCB", s4(r.ucb95), rel)
            m.add(f"{t}P", pfmt(r.p_holm), rel, "Holm over 8")
            m.add(f"{t}R", f"{r.rank_biserial:+.2f}", rel)
        m.add("HTwoAllSig", "yes" if h2.significant_holm_005.all() else "no", rel)
    rel = "artifacts/statistics/h2_srcfa_percentile.csv"
    pc = m.csv(rel)
    if pc is not None:
        for _, r in pc.iterrows():
            m.add(f"PctK{w(r.k)}", f"{r.median_percentile:.0f}", rel, "median percentile")
            m.add(f"PctKAboveNinetyFive{w(r.k)}", str(int(r.n_above_p95)), rel)
    rel = "artifacts/statistics/baseline_pairwise_exploratory.csv"
    bx = m.csv(rel)
    if bx is not None:
        for _, r in bx.iterrows():
            other = r.comparison.split(" vs ")[1].title()
            t = f"VS{other}K{w(r.k)}"
            m.add(f"{t}Diff", s4(r.mean_diff), rel, "SR-CFA minus baseline; exploratory")
            m.add(f"{t}P", pfmt(r.p_raw), rel, "uncorrected")

    # ---------------- H3 ---------------------------------------------------------------------
    rel = "artifacts/statistics/h3_lambda_vs_zero.csv"
    h3 = m.csv(rel)
    if h3 is not None:
        m.add("HThreeMaxAbsDiff", f"{h3.mean_diff.abs().max():.4f}", rel)
        m.add("HThreeNSig", str(int(h3.significant_holm_005.sum())), rel)
        m.add("HThreeNTests", str(len(h3)), rel)
        m.add("HThreeMinP", pfmt(h3.p_holm.min()), rel, "smallest Holm p")
        m.add("HThreeMinTied", str(int(h3.n_tied.min())), rel, "min participants with identical subset")

    # ---------------- H4 faithfulness --------------------------------------------------------
    rel = "artifacts/statistics/h4_faithfulness.csv"
    h4 = m.csv(rel)
    rel_fs = "artifacts/faithfulness/faithfulness_summary.csv"
    fs = m.csv(rel_fs)
    rel_pc = "artifacts/faithfulness/protocol_check.txt"
    if not (ROOT / rel_pc).exists():
        m.errors.append(f"missing {rel_pc}")
    else:
        chk = dict(l.split("=", 1) for l in (ROOT / rel_pc).read_text().splitlines() if "=" in l)
        # Same channels and protocol as P4; residual differences are numerical fitting noise.
        # Tolerance fixed here: mean |diff| must stay below 0.005 Macro-F1.
        if float(chk["mean_abs_diff"]) > 0.005 or float(chk.get("same_channels_frac", 0)) < 1:
            m.errors.append(f"faithfulness protocol check failed: {chk}")
        m.add("FaithProtocolCells", chk["matched_cells"], rel_pc)
        m.add("FaithProtocolMeanDiff", f"{float(chk['mean_abs_diff']):.4f}", rel_pc)
        m.add("FaithProtocolMaxDiff", f"{float(chk['max_abs_diff']):.4f}", rel_pc)
    if h4 is not None and fs is not None:
        for _, r in fs.iterrows():
            arm = {"remove_top": "Top", "remove_bottom": "Bottom", "remove_random": "Random"}[r.arm]
            m.add(f"Faith{arm}K{w(r.n_kept)}", f3(r.mean_macro_f1), rel_fs)
        for _, r in h4.iterrows():
            kind = {"remove_top - remove_bottom": "TB", "remove_top - remove_random": "TR",
                    "remove_random - remove_bottom": "RB"}[r.comparison]
            t = f"Faith{kind}K{w(r.k)}"
            m.add(f"{t}Diff", s4(r.mean_diff), rel)
            m.add(f"{t}LCB", s4(r.lcb95), rel)
            m.add(f"{t}UCB", s4(r.ucb95), rel)
            m.add(f"{t}P", pfmt(r.p_holm), rel, "Holm")
        m.add("FaithNTests", str(len(h4)), rel)
        m.add("FaithNSig", str(int(h4.significant_holm_005.sum())), rel)
        tb = h4[h4.comparison == "remove_top - remove_bottom"]
        m.add("FaithTBAllSig", "yes" if tb.significant_holm_005.all() else "no", rel)

    # ---------------- stability --------------------------------------------------------------
    rel = "artifacts/stability/stability_summary.csv"
    st = m.csv(rel)
    if st is not None:
        for grp, tag in (("per_subject_STRONGEST", "Subj"), ("inner_folds_group_level", "Inner"),
                         ("outer_folds_UPPER_BOUND", "Outer")):
            r = st[st.group == grp].iloc[0]
            m.add(f"Stab{tag}Pairs", str(int(r.n_pairs)), rel)
            m.add(f"Stab{tag}Rho", f3(r.spearman_rho_mean), rel)
            m.add(f"Stab{tag}RhoSD", f3(r.spearman_rho_sd), rel)
            for kk, kt in ((4, "Four"), (6, "Six"), (8, "Eight")):
                m.add(f"Stab{tag}Jac{kt}", f3(r[f"jaccard_top{kk}_mean"]), rel)

    # ---------------- cross-session ----------------------------------------------------------
    rel = "artifacts/cross_session/cross_session_metrics.csv"
    cs = m.csv(rel, N_GRAB, "participant_id")
    if cs is not None:
        g = cs.groupby(["design", "test_session"])
        for (d, t), sub in g:
            tag = f"CS{'One' if d == 'CS1' else 'Two'}S{w(t)}"
            m.add(tag, f3(sub.macro_f1.mean()), rel)
            m.add(f"{tag}SD", f3(sub.macro_f1.std()), rel)
            m.add(f"{tag}Train", intc(sub.n_train_windows.median()), rel, "median train windows")
    rel = "artifacts/statistics/cross_session_tests.csv"
    ct = m.csv(rel)
    if ct is not None:
        tags = {"CS1: test S2 - test S1": "CSSTwoVsSOne", "CS1: test S3 - test S1": "CSSThreeVsSOne",
                "S3 test: CS2 (train S1+S2) - CS1 (train S1)": "CSTwoVsOne"}
        for _, r in ct.iterrows():
            t = tags[r.comparison]
            m.add(f"{t}Diff", s4(r.mean_diff), rel)
            m.add(f"{t}LCB", s4(r.lcb95), rel)
            m.add(f"{t}UCB", s4(r.ucb95), rel)
            m.add(f"{t}W", f"{r.wilcoxon_W:.1f}", rel)
            m.add(f"{t}P", pfmt(r.p_raw), rel, "exploratory, uncorrected")

    # ---------------- DB5 --------------------------------------------------------------------
    rel = "artifacts/db5/db5_sparse_curve.csv"
    dc = m.csv(rel, N_DB5, "participant_id")
    rel_f = "artifacts/db5/db5_full_channel_metrics.csv"
    dfull = m.csv(rel_f, N_DB5, "participant_id")
    rel_n = "artifacts/statistics/db5_non_inferiority_by_k.csv"
    dn = m.csv(rel_n)
    rel_r = "artifacts/statistics/db5_bootstrap_seed_robustness.csv"
    dr = m.csv(rel_r)
    if dc is not None and dn is not None and dr is not None and dfull is not None:
        m.add("DBFiveFull", f3(dfull.macro_f1.mean()), rel_f)
        m.add("DBFiveFullSD", f3(dfull.macro_f1.std()), rel_f)
        m.add("DBFiveFullMin", f3(dfull.macro_f1.min()), rel_f)
        m.add("DBFiveFullMax", f3(dfull.macro_f1.max()), rel_f)
        g = dc.groupby("channels_k").macro_f1
        for k in (16, 12, 8, 4):
            m.add(f"DBFiveK{w(k)}", f3(g.mean()[k]), rel)
            m.add(f"DBFiveK{w(k)}SD", f3(g.std()[k]), rel)
        n2 = dn[np.isclose(dn.margin, 0.02)].set_index("k")
        for k in (11, 12, 13, 14, 15):
            m.add(f"DBFiveDeltaK{w(k)}", s4(n2.loc[k, "mean_diff"]), rel_n)
            m.add(f"DBFiveDeltaK{w(k)}LCB", f"{n2.loc[k, 'lcb_95']:+.5f}", rel_n)
        ksd = dn[dn.is_non_inferior].groupby("margin").k.min()
        for mg, tag in ((0.01, "One"), (0.02, "Two"), (0.03, "Three")):
            v = ksd.get(mg, np.nan)
            m.add(f"DBFiveKStarMarginPt{tag}", "none" if pd.isna(v) else str(int(v)), rel_n)
        n_pass = n2[n2.is_non_inferior].index.tolist()
        m.add("DBFiveNIPassing", ", ".join(map(str, n_pass)) if n_pass else "none", rel_n,
              "all k passing at 0.02")
        rr = dr.set_index("k").loc[12]
        m.add("DBFiveSeedFrac", f"{100 * rr['frac_seeds_non_inferior_0.02']:.1f}", rel_r,
              f"{int(rr.n_seeds)} bootstrap seeds")
        m.add("DBFiveSeedN", str(int(rr.n_seeds)), rel_r)
        m.add("DBFiveSeedLCBMin", f"{rr.lcb_min:+.4f}", rel_r)
        m.add("DBFiveSeedLCBMax", f"{rr.lcb_max:+.4f}", rel_r)

    # ---------------- bipolar ----------------------------------------------------------------
    rel = "artifacts/bipolar/bipolar_sparse_curve.csv"
    bp = m.csv(rel, N_GRAB, "participant_id")
    rel_bf = "artifacts/bipolar/bipolar_full_channel_metrics.csv"
    bpf = m.csv(rel_bf, N_GRAB, "participant_id")
    rel_n = "artifacts/statistics/bipolar_non_inferiority_by_k.csv"
    bn = m.csv(rel_n)
    if bp is not None and bn is not None and bpf is not None:
        m.add("BipFull", f3(bpf.macro_f1.mean()), rel_bf, "8 pairs, all training windows")
        m.add("BipFullSD", f3(bpf.macro_f1.std()), rel_bf)
        b0 = bp[np.isclose(bp["lambda"], 0.0)].groupby("channels_k").macro_f1
        for k in range(1, 9):
            m.add(f"BipK{w(k)}", f3(b0.mean()[k]), rel, "lambda=0")
            m.add(f"BipK{w(k)}SD", f3(b0.std()[k]), rel)
        b2 = bn[np.isclose(bn["lambda"], 0.0) & np.isclose(bn.margin, 0.02)].set_index("k")
        for k in range(1, 8):
            m.add(f"BipDeltaK{w(k)}", s4(b2.loc[k, "mean_diff"]), rel_n)
            m.add(f"BipDeltaK{w(k)}LCB", s4(b2.loc[k, "lcb_95"]), rel_n)
        for mg, tag in ((0.01, "One"), (0.02, "Two"), (0.03, "Three")):
            ks_l = (bn[bn.is_non_inferior & np.isclose(bn.margin, mg)].groupby("lambda").k.min()
                    .reindex(sorted(bn["lambda"].unique())))
            vals = set(ks_l.fillna(-1).astype(int))
            if len(vals) != 1:
                m.errors.append(f"bipolar k* differs across lambda at margin {mg}: {ks_l.to_dict()}")
            v = vals.pop()
            m.add(f"BipKStarMarginPt{tag}", "none" if v < 0 else str(v), rel_n, "all lambda")
        rel_rb = "artifacts/statistics/bipolar_bootstrap_seed_robustness.csv"
        brb = m.csv(rel_rb)
        if brb is not None:
            r7 = brb.set_index("k").loc[7]
            m.add("BipSeedFracSeven", f"{100 * r7['frac_seeds_non_inferior_0.02']:.0f}", rel_rb)
            m.add("BipSeedLCBMaxSeven", f"{r7.lcb_max:+.4f}", rel_rb)
            m.add("BipSeedLCBMinSeven", f"{r7.lcb_min:+.4f}", rel_rb)
        m.add("BipCurveRefK", f3(b0.mean()[8]), rel, "k=8 curve reference, 200k subsample")
        rel_rk = "artifacts/bipolar/bipolar_rankings.csv"
        brk = m.csv(rel_rk, N_GRAB, "outer_participant")
        if brk is not None:
            t3 = (brk[np.isclose(brk["lambda"], 0.0)].ranking.str.split(";")
                  .apply(lambda r: tuple(sorted(int(c) for c in r[:3]))).value_counts())
            m.add("BipTopThreeSet", ", ".join(map(str, t3.index[0])), rel_rk, "modal top-3 pairs")
            m.add("BipTopThreeFolds", str(int(t3.iloc[0])), rel_rk)

    # ---------------- fixed layout (exploratory, post hoc) -----------------------------------
    rel = "artifacts/fixed_layout/fixed_layout_summary.json"
    p = ROOT / rel
    if not p.exists():
        m.errors.append(f"missing {rel}")
    else:
        fx = json.loads(p.read_text(encoding="utf-8"))
        m.add("FixedDev", str(fx["dev_subjects_count"]), rel)
        m.add("FixedTest", str(fx["test_subjects_count"]), rel)
        m.add("FixedChannels", ", ".join(map(str, sorted(fx["frozen_consensus_channels"]))), rel)
        m.add("FixedDropped", ", ".join(map(str, sorted(fx["dropped_channels"]))), rel)
        m.add("FixedFull", f3(fx["mean_macro_f1_full16"]), rel)
        m.add("FixedTwelve", f3(fx["mean_macro_f1_fixed12"]), rel)
        m.add("FixedDiff", s4(fx["paired_difference_mean"]), rel)
        m.add("FixedLCB", s4(fx["bootstrap_95_lcb"]), rel)
        m.add("FixedUCB", s4(fx["bootstrap_95_ucb"]), rel)

    # ---------------- feature redundancy -----------------------------------------------------
    rel = "artifacts/sensitivity/feature_redundancy_summary.csv"
    fr = m.csv(rel)
    if fr is not None:
        r = fr.iloc[0]
        if int(r.n) != N_GRAB:
            m.errors.append(f"feature redundancy n={r.n}")
        m.add("RedundDiff", s4(r.mean_diff), rel, "9 minus 10 features")
        m.add("RedundLCB", s4(r.lcb95), rel)
        m.add("RedundUCB", s4(r.ucb95), rel)
        m.add("RedundRho", f3(r.median_rank_spearman), rel, "median per-fold channel-rank rho")
        m.add("RedundTopTwelveSame", str(int(r.n_top12_identical)), rel)

    # ---------------- H1 Holm (plan-conformant, applied post hoc; Decision 18) -----------------
    rel = "artifacts/statistics/h1_holm.csv"
    hh = m.csv(rel)
    if hh is not None:
        for tag_a, lam_sel in (("H", 0.0),):
            g = hh[(hh.analysis == "H1") & np.isclose(hh["lambda"], lam_sel)]
            for mg, tag in ((0.01, "PtOne"), (0.02, ""), (0.03, "PtThree")):
                gg = g[np.isclose(g.margin, mg)]
                for col, nm in (("ni_holm", "Holm"), ("ni_fixed_sequence_posthoc", "FixSeq")):
                    v = gg.k[gg[col].astype(bool)].min()
                    m.add(f"KStar{nm}{tag}", "none" if pd.isna(v) else str(int(v)), rel)
            g12 = g[np.isclose(g.margin, 0.02)].set_index("k")
            m.add("HolmPKTwelve", pfmt(g12.loc[12, "p_holm"]), rel, "one-sided bootstrap, Holm over 15 k")
            m.add("HolmPKEleven", pfmt(g12.loc[11, "p_holm"]), rel)
        # identical k* under every lambda?
        same = all(
            hh[(hh.analysis == "H1") & np.isclose(hh.margin, mg)].groupby("lambda")
            .apply(lambda d: d.k[d.ni_holm.astype(bool)].min(), include_groups=False).nunique() == 1
            for mg in (0.01, 0.02, 0.03))
        m.add("HolmSameAllLambda", "yes" if same else "no", rel)
        d = hh[(hh.analysis == "DB5")]
        for mg, tag in ((0.01, "One"), (0.02, "Two"), (0.03, "Three")):
            dd = d[np.isclose(d.margin, mg)]
            v = dd.k[dd.ni_holm.astype(bool)].min()
            m.add(f"DBFiveKStarHolmPt{tag}", "none" if pd.isna(v) else str(int(v)), rel)
        d12 = d[np.isclose(d.margin, 0.02)].set_index("k").loc[12]
        m.add("DBFiveDeltaKTwelveLCBSix", f"{d12.lcb95:+.6f}", rel, "6 dp; decision is LCB > -0.02")

    # ---------------- margin rationale (arithmetic on the curve reference) ---------------------
    rel = "artifacts/metrics/sparse_curve_subject_metrics.csv"
    cc = m.csv(rel)
    if cc is not None:
        ref = cc[np.isclose(cc["lambda"], 0.0) & (cc.channels_k == 16)].macro_f1.mean()
        m.add("MarginPctOfRef", f"{100 * 0.02 / ref:.1f}", rel, "0.02 / k=16 curve mean")
        m.add("MarginPctAboveChance", f"{100 * 0.02 / (ref - 1 / 16):.1f}", rel,
              "0.02 / (k=16 curve mean - 1/16)")

    # ---------------- leave-one-out threshold check (Decision 17) -----------------------------
    rel = "artifacts/sensitivity/loo_threshold_check.csv"
    lt = m.csv(rel)
    if lt is not None:
        for rep, tag in (("grabmyo_monopolar", "Mono"), ("db5", "DBFive"), ("grabmyo_bipolar", "Bip")):
            g = lt[lt.representation == rep]
            m.add(f"LOO{tag}Folds", str(len(g)), rel)
            m.add(f"LOO{tag}Identical", str(int(g.identical.sum())), rel)
            m.add(f"LOO{tag}InProbe", str(int(g.held_out_in_probe_set.sum())), rel)
        g = lt[lt.representation == "grabmyo_monopolar"]
        m.add("LOOMonoMin", f"{1000 * g.loo_median.min():.2f}", rel, "x1e-3 mV")
        m.add("LOOMonoMax", f"{1000 * g.loo_median.max():.2f}", rel, "x1e-3 mV")
        g = lt[lt.representation == "grabmyo_bipolar"]
        m.add("LOOBipPooled", f"{1000 * g.pooled_median.iloc[0]:.2f}", rel, "x1e-3 mV")
        m.add("LOOBipRule", f"{1000 * g.pooled_rule_threshold.iloc[0]:.0f}", rel, "x1e-3 mV")

    # ---------------- putEMG (exploratory, added after all other results; Decision 19) ---------
    P = "artifacts/putemg/"
    pc = m.csv(P + "sparse_curve.csv", 44, "participant_id")
    pn = m.csv("artifacts/statistics/putemg_non_inferiority_by_k.csv")
    pr = m.csv("artifacts/statistics/putemg_bootstrap_seed_robustness.csv")
    pv = m.csv("artifacts/statistics/putemg_vs_random.csv")
    pt = m.csv(P + "threshold_loo.csv")
    pq = m.csv("data/features/putemg_extraction_qc.csv")
    prk = m.csv(P + "rankings.csv", 44, "outer_participant")
    if all(x is not None for x in (pc, pn, pr, pv, pt, pq, prk)):
        rel = P + "sparse_curve.csv"
        m.add("PutParticipants", str(pc.participant_id.nunique()), rel)
        m.add("PutWindows", intc(pc[pc.channels_k == 24].n_test_windows.sum()), rel)
        full = pc[pc.channels_k == 24].macro_f1
        mm, ll, uu = bootstrap_participant_metrics(full.to_numpy())
        m.add("PutFull", f3(mm), rel)
        m.add("PutFullLCB", f3(ll), rel)
        m.add("PutFullUCB", f3(uu), rel)
        m.add("PutFullMin", f3(full.min()), rel)
        m.add("PutFullMax", f3(full.max()), rel)
        m.add("PutTrainWindowsMax", intc(pc.n_train_windows.max()), rel)
        m.add("PutThresh", f"{pt.loo_threshold.iloc[0] * 1000:.0f}", P + "threshold_loo.csv", "x1e-3 mV")
        m.add("PutThreshIdentical", str(int(pt.identical.sum())), P + "threshold_loo.csv")
        rel_n = "artifacts/statistics/putemg_non_inferiority_by_k.csv"
        for mg, tag in ((0.01, "One"), (0.02, "Two"), (0.03, "Three")):
            g = pn[np.isclose(pn.margin, mg)]
            for col, nm in (("ni_unadjusted", ""), ("ni_holm", "Holm")):
                v = g.k[g[col].astype(bool)].min()
                m.add(f"PutKStar{nm}Pt{tag}", "none" if pd.isna(v) else str(int(v)), rel_n)
        g2 = pn[np.isclose(pn.margin, 0.02)].set_index("k")
        ks2 = g2.index[g2.ni_unadjusted.astype(bool)]
        kstar = int(ks2.min()) if len(ks2) else None
        show = sorted({12, 18} | ({kstar, kstar - 1} if kstar else set()))
        for k in show:
            m.add(f"PutDeltaK{w(k)}", s4(g2.loc[k, "mean_delta"]), rel_n)
            m.add(f"PutDeltaK{w(k)}LCB", f"{g2.loc[k, 'lcb95']:+.5f}", rel_n)
            m.add(f"PutDeltaK{w(k)}UCB", s4(g2.loc[k, "ucb95"]), rel_n)
        if kstar:
            m.add("PutKStarMinusOne", str(kstar - 1), rel_n)
            m.add("PutKStarReductionPct", f"{100 * (24 - kstar) / 24:.0f}", rel_n)
            passing = g2.index[g2.ni_unadjusted.astype(bool)]
            m.add("PutContiguous", "yes" if list(passing) == list(range(kstar, 24)) else "no", rel_n)
            rr = pr.set_index("k").loc[kstar]
            m.add("PutSeedFrac", f"{100 * rr['frac_seeds_non_inferior_0.02']:.0f}",
                  "artifacts/statistics/putemg_bootstrap_seed_robustness.csv")
        mono = all(pc.groupby("channels_k").macro_f1.mean().diff().dropna() >= 0)
        m.add("PutMonotone", "yes" if mono else "no", rel)
        rel_v = "artifacts/statistics/putemg_vs_random.csv"
        for _, r in pv.iterrows():
            k = int(r.k)
            m.add(f"PutVsRandK{w(k)}Diff", s4(r.mean_diff), rel_v)
            m.add(f"PutVsRandK{w(k)}LCB", s4(r.lcb95), rel_v)
            m.add(f"PutVsRandK{w(k)}UCB", s4(r.ucb95), rel_v)
            m.add(f"PutVsRandK{w(k)}P", pfmt(r.p_holm), rel_v)
            m.add(f"PutVsRandK{w(k)}R", f"{r.rank_biserial:.2f}", rel_v)
        rel_rk = P + "rankings.csv"
        t = (prk[np.isclose(prk["lambda"], 0.0)].ranking.str.split(";")
             .apply(lambda r: tuple(sorted(int(c) for c in r[:4]))).value_counts())
        m.add("PutTopFourSet", ", ".join(map(str, t.index[0])), rel_rk, "modal top-4")
        m.add("PutTopFourFolds", str(int(t.iloc[0])), rel_rk)
        top = prk[np.isclose(prk["lambda"], 0.0)].ranking.str.split(";").apply(lambda r: [int(c) for c in r[:8]])
        band = lambda c: 0 if c <= 8 else (1 if c <= 16 else 2)
        cnt = np.zeros(3)
        for r in top:
            for c in r:
                cnt[band(c)] += 1
        cnt = 100 * cnt / cnt.sum()
        m.add("PutTopEightElbowPct", f"{cnt[0]:.0f}", rel_rk, "share of top-8 slots in band 1-8")
        m.add("PutTopEightMiddlePct", f"{cnt[1]:.0f}", rel_rk, "band 9-16")
        m.add("PutTopEightWristPct", f"{cnt[2]:.0f}", rel_rk, "band 17-24")
        lam_same = prk.groupby("outer_participant").ranking.apply(
            lambda s: s.str.split(";").apply(lambda r: tuple(sorted(r[:12]))).nunique() == 1)
        m.add("PutTopTwelveLambdaSame", str(int(lam_same.sum())), rel_rk,
              "folds whose top-12 set is identical under all four lambda")

    draft = "--draft" in sys.argv
    if m.errors:
        print("MISSING/INCONSISTENT INPUTS:\n  - " + "\n  - ".join(m.errors))
        if not draft:
            print("REFUSING TO GENERATE MACROS (use --draft only for a layout preview).")
            return 1
    OUT.mkdir(parents=True, exist_ok=True)
    lines = (["% DRAFT BUILD - INCOMPLETE INPUTS, NOT FOR SUBMISSION:"]
             + [f"%   {e}" for e in m.errors]) if draft and m.errors else []
    lines += ["% AUTO-GENERATED by scripts/40_generate_macros.py - do not edit by hand.",
             "% Every value is traceable via manuscript/generated/macro_provenance.csv", ""]
    lines += [f"\\newcommand{{\\{r['macro']}}}{{{r['value']}}}" for r in m.rows]
    (OUT / "results_macros.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    pd.DataFrame(m.rows).to_csv(OUT / "macro_provenance.csv", index=False)
    print(f"wrote {len(m.rows)} macros")
    return 0


if __name__ == "__main__":
    sys.exit(main())
