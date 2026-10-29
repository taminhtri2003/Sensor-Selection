"""Language pass on table captions and headers in scripts/42_generate_tables.py (2026-09-22):
removes code-like shorthand (200k, 150k, LCB, NI, arm, draws) and process wording (post hoc
narrative) from captions. Values are untouched."""
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "scripts" / "42_generate_tables.py"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert a in s, a[:60]
    s = s.replace(a, b)


rep('''    budget = {"M_XGBoost": "all ($\\\\approx$550k)", "M_SVM": "40k", "M_RandomForest": "200k"}''',
    '''    budget = {"M_XGBoost": "all", "M_SVM": "40{,}000", "M_RandomForest": "200{,}000"}''')
rep('''"participants; every $k$ retrained from scratch on a fixed 200k-window outer-training "
          "subsample). $\\\\Delta_k$''', '''"participants; every $k$ retrained from scratch on the same 200,000 training windows of "
          "each fold). $\\\\Delta_k$''')
rep('''B("Holm: non-inferiority at $\\\\delta = 0.02$ after the plan's Holm correction "
          "over the 15 tested $k$, applied post hoc (Supplementary Table~\\\\ref{tab:h1_holm}).")''',
    '''B("Holm: non-inferiority at $\\\\delta = 0.02$ after Holm correction over the 15 subset "
          "sizes (Table~\\\\ref{tab:h1_holm}).")''')
rep('''    rows.append(["SR-CFA percentile in random draws (median)"] + [
        f"{pc.loc[k, 'median_percentile']:.0f} ({int(pc.loc[k, 'n_draws'])} draws)" for k in ks])''',
    '''    rows.append([B("SR-CFA percentile among random subsets (median)")] + [
        f"{pc.loc[k, 'median_percentile']:.0f} (" + B(f"{int(pc.loc[k, 'n_draws'])} subsets") + ")"
        for k in ks])''')
rep('''"comparison model (XGBoost, 50 trees, 150k-window outer-training subsample), so values "''',
    '''"comparison model (XGBoost, 50 trees, 150,000 training windows per fold), so values "''')
rep('''"Deletion (remove-and-retrain) faithfulness test (H4; 43 participants). Every arm uses the "
          "same comparison model and training subsample; " + B("Remove-Random") + " averages 100 (500 at "
          "$k$ = 12) draws per participant and exists only where those draws were sampled. "''',
    '''"Deletion (remove-and-retrain) faithfulness test (H4; 43 participants). " + B("All deletion "
          "orders use the same comparison model and training sample; Remove-Random averages 100 "
          "random subsets per participant (500 at 12 channels) and is available only where these "
          "were sampled. ")''')
rep('''"Comparison & Pairs & Spearman $\\\\rho$ & Kendall $\\\\tau$ & Jaccard@4 & Jaccard@6 & Jaccard@8",''',
    '''"Comparison & Pairs & Spearman $\\\\rho$ & Kendall $\\\\tau$ & " + B("Jaccard, top 4 & Jaccard, top 6 & Jaccard, top 8"),''')
rep('''"LCB to 6 decimals because the $k = 12$ decision lies at the margin. NI = lower bound "
            "above $-\\\\delta$ (primary, uncorrected); Holm = after Holm correction over 15 $k$; "
            "seeds = share of 200 alternative bootstrap seeds under which $k$ is non-inferior."),
          "tab:replication", "rcccccc",
          "$k$ & Macro-F1 & $\\\\Delta_k$ & LCB & NI & Holm & Seeds NI", rows, star=False)''',
    '''"Lower 95\\\\% bound shown to six decimals because the $k = 12$ decision lies at the margin. "
            "Non-inferior: lower bound above $-\\\\delta$ (uncorrected), and after Holm correction over "
            "15 subset sizes; bootstrap seeds: share of 200 alternative seeds under which $k$ is "
            "non-inferior."),
          "tab:replication", "rcccccc",
          "$k$ & Macro-F1 & $\\\\Delta_k$ & Lower bound & Non-inf. & Non-inf. (Holm) & Bootstrap seeds",
          rows, star=False)''')
rep('''"$\\\\lambda = 0$). Reference = $k = 8$ model of the same curve (200k-window subsample), "
            "mean Macro-F1 " + f3(bp.mean_ref.iloc[0]) + "; margin $\\\\delta = 0.02$."),
          "tab:bipolar", "rccccc",
          "$k$ & Macro-F1 & $\\\\Delta_k$ & 95\\\\% CI & NI & Seeds NI", rows, star=False)''',
    '''"$\\\\lambda = 0$). Reference = $k = 8$ model of the same curve (200,000 training windows), "
            "mean Macro-F1 " + f3(bp.mean_ref.iloc[0]) + "; margin $\\\\delta = 0.02$; bootstrap "
            "seeds: share of 200 alternative seeds under which $k$ is non-inferior."),
          "tab:bipolar", "rccccc",
          "$k$ & Macro-F1 & $\\\\Delta_k$ & 95\\\\% CI & Non-inf. & Bootstrap seeds", rows, star=False)''')
rep('''else "; not identical across $\\\\lambda$ (see artifacts/statistics/h1_holm.csv).")''',
    '''else "; not identical across all $\\\\lambda$.")''')
rep('''B("H1 with the plan's Holm correction (applied post hoc; 43 participants, $\\\\lambda = 0$, "''',
    '''B("H1 with Holm correction over the 15 subset sizes (43 participants, $\\\\lambda = 0$, "''')
rep('''"$\\\\alpha = 0.025$. Fixed sequence (post-hoc sensitivity): $k = 15, 14, \\\\ldots$ tested "
            "in order, stopping at the first failure."),
          "tab:h1_holm", "rccccccc",
          "$k$ & $\\\\bar\\\\Delta_k$ & LCB & $p$ & $p_{\\\\mathrm{Holm}}$ & NI & NI Holm & Fixed seq.",''',
    '''"$\\\\alpha = 0.025$. Fixed sequence (sensitivity analysis): $k = 15, 14, \\\\ldots$ tested "
            "in order, stopping at the first failure."),
          "tab:h1_holm", "rccccccc",
          "$k$ & $\\\\bar\\\\Delta_k$ & Lower bound & $p$ & $p_{\\\\mathrm{Holm}}$ & Non-inf. & "
          "Non-inf. (Holm) & Fixed sequence",''')
rep('''B("putEMG sparse curve (exploratory, added post hoc; 44 participants, 24 monopolar "''',
    '''B("putEMG sparse curve (exploratory replication; 44 participants, 24 monopolar "''')
rep('''"Macro-F1 " + f3(pcur.mean()[24]) + "; margin $\\\\delta = 0.02$). NI = lower bound above "
            "$-\\\\delta$; Holm over 23 $k$; seeds = share of 200 alternative bootstrap seeds."),
          "tab:putemg", "rcccccc",
          "$k$ & Macro-F1 & $\\\\bar\\\\Delta_k$ & 95\\\\% CI & NI & Holm & Seeds NI", rows, star=False,''',
    '''"Macro-F1 " + f3(pcur.mean()[24]) + "; margin $\\\\delta = 0.02$). Non-inferior: lower bound "
            "above $-\\\\delta$ (uncorrected), and after Holm correction over 23 subset sizes; "
            "bootstrap seeds: share of 200 alternative seeds under which $k$ is non-inferior."),
          "tab:putemg", "rcccccc",
          "$k$ & Macro-F1 & $\\\\bar\\\\Delta_k$ & 95\\\\% CI & Non-inf. & Non-inf. (Holm) & "
          "Bootstrap seeds", rows, star=False,''')
p.write_text(s, encoding="utf-8")
print("table language patched")
