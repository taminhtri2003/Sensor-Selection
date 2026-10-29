"""Claim-evidence matrix: each substantive claim in the manuscript, the macros that carry its
numbers, and the result files those macros come from (via macro_provenance.csv). Values are read
from provenance, never typed here."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
prov = pd.read_csv(ROOT / "manuscript/generated/macro_provenance.csv").set_index("macro")

CLAIMS = [
    ("Abstract/Results", "confirmatory", "XGBoost full-channel Macro-F1 with 95% CI", ["FullXGB", "FullXGBLCB", "FullXGBUCB"]),
    ("Results", "confirmatory", "No statistically detectable XGBoost-SVM difference (not equivalence)", ["XGBvsSVMDiff", "XGBvsSVMP"]),
    ("Results", "confirmatory", "Both exceed random forest", ["XGBvsRFP", "SVMvsRFP"]),
    ("Abstract/Results", "H1", "k* = 12 at delta 0.02", ["KStar", "DeltaKTwelve", "DeltaKTwelveLCB"]),
    ("Results", "H1", "k = 11 fails the margin", ["DeltaKElevenLCB"]),
    ("Abstract/Results", "H1", "k* under sensitivity margins", ["KStarMarginPtOne", "KStarMarginPtThree"]),
    ("Results", "H1", "Top-4 electrodes stable across folds", ["TopFourSet", "TopFourFolds", "TopFourShare"]),
    ("Abstract/Results", "H2", "Attribution beats random at k = 4, 6, 8, 12", ["HTwoKSixDiff", "HTwoKSixP", "HTwoKTwelveP", "HTwoAllSig"]),
    ("Results", "H2", "SR-CFA rarely at top of the random distribution", ["PctKSix", "PctKAboveNinetyFiveSix"]),
    ("Abstract/Results", "exploratory", "No statistically detectable difference geometric vs attribution at k = 4, 8, 12 (exploratory; not equivalence)", ["VSGeomKFourP", "VSGeomKEightP", "VSGeomKTwelveP", "VSGeomKSixP"]),
    ("Abstract/Results", "H3", "Stability penalty: no measurable benefit", ["HThreeNSig", "HThreeMaxAbsDiff", "UOverAMedian", "TopTwelveDiffersLambdaOne"]),
    ("Abstract/Results", "H4", "Deletion ordering supports faithfulness", ["FaithNSig", "FaithNTests", "FaithTRKSixP", "FaithRBKSixP"]),
    ("Methods", "H4", "Faithfulness protocol matches P4", ["FaithProtocolCells", "FaithProtocolMeanDiff"]),
    ("Results", "exploratory", "Ranking agreement between participants", ["StabSubjRho", "StabSubjJacSix"]),
    ("Results", "exploratory", "No additional cross-day loss; CS2 gain confounded", ["CSSTwoVsSOneP", "CSSThreeVsSOneP", "CSTwoVsOneDiff"]),
    ("Results", "exploratory", "DB5 k = 12 fragile", ["DBFiveKStarMarginPtTwo", "DBFiveDeltaKTwelveLCB", "DBFiveSeedFrac", "DBFiveDeltaKThirteenLCB"]),
    ("Results/Discussion", "exploratory", "Bipolar non-inferiority outcome at delta 0.02", ["BipKStarMarginPtTwo", "BipDeltaKSevenLCB", "BipSeedFracSeven"]),
    ("Results", "post hoc", "Fixed-layout consistency check; electrode count informed by full-cohort results", ["FixedDiff", "FixedLCB"]),
    ("Results", "exploratory", "IEMG removal: little measurable effect on ranking", ["RedundDiff", "RedundRho"]),
    ("Results/Suppl.", "H1 (post hoc Holm)", "k* unchanged under the plan's Holm correction", ["KStarHolm", "KStarHolmPtOne", "KStarHolmPtThree", "HolmPKTwelve"]),
    ("Results", "exploratory", "DB5 k* = none after Holm", ["DBFiveKStarHolmPtTwo", "DBFiveDeltaKTwelveLCBSix"]),
    ("Methods", "leakage check (post hoc)", "Count threshold identical in every LOO fold", ["LOOMonoIdentical", "LOOMonoFolds", "LOODBFiveIdentical"]),
    ("Methods", "design", "Margin as share of reference and of distance above chance", ["MarginPctOfRef", "MarginPctAboveChance"]),
    ("Methods", "design", "SVM likely a lower bound (one calibration fold)", ["SVMCalibTwentyK", "SVMCalibFortyK"]),
]


def main():
    rows = []
    for where, kind, claim, macros in CLAIMS:
        missing = [m for m in macros if m not in prov.index]
        if missing:
            print(f"FATAL: claim '{claim}' uses undefined macros {missing}")
            return 1
        rows.append({"location": where, "type": kind, "claim": claim,
                     "values": "; ".join(f"{m}={prov.loc[m, 'value']}" for m in macros),
                     "sources": "; ".join(sorted({prov.loc[m, 'source'] for m in macros}))})
    out = ROOT / "reports" / "claim_evidence_matrix.csv"
    folder=ROOT/'artifacts/participant_attribution'
    penalty=pd.read_csv(folder/'penalty_gate.csv')
    paired=pd.read_csv(folder/'paired_comparisons.csv')
    summary=pd.read_csv(folder/'report_summary.csv')
    rows.append({'location':'Abstract/Results/Discussion','type':'post hoc',
                 'claim':'Participant-level penalty benefit and harm under the complete corrected family',
                 'values':f'tests={len(penalty)}; benefit={int(penalty.supports_penalty_benefit.sum())}; harm={int(penalty.supports_penalty_harm.sum())}',
                 'sources':'artifacts/participant_attribution/penalty_gate.csv'})
    rows.append({'location':'Results/Figure 9','type':'post hoc',
                 'claim':'Participant versus fold aggregation under family-wide correction',
                 'values':f'tests={len(paired)}; significant={int((paired.p_holm<.05).sum())}',
                 'sources':'artifacts/participant_attribution/paired_comparisons.csv'})
    rows.append({'location':'Supplementary table','type':'post hoc',
                 'claim':'All candidate non-inferiority results for the upgraded aggregation',
                 'values':summary.to_json(orient='records'),
                 'sources':'artifacts/participant_attribution/report_summary.csv'})
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"wrote {len(rows)} claims to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
