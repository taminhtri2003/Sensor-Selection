"""Patch scripts/42_generate_tables.py for the 2026-09-21 revision (audit H-table items).
Original archived at _archive_invalid/42_generate_tables_before_revision.py."""
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "scripts" / "42_generate_tables.py"
s = p.read_text(encoding="utf-8")


def rep(a, b):
    global s
    assert a in s, a[:60]
    s = s.replace(a, b)


rep('''def f3(x):
    return f"{x:.3f}"
''', '''def f3(x):
    return f"{x:.3f}"


def B(x):
    """cell changed in the 2026-09-21 revision (blue when highlighting is on)"""
    return f"\\\\rev{{{x}}}"
''')
rep('''            row += ["reference", "", "", "", ""]''', '''            row += ["reference", "", "", "", "", ""]''')
rep('''            for mg in (0.01, 0.02, 0.03):
                ok = ni[(ni.k == k) & np.isclose(ni.margin, mg)].iloc[0].is_non_inferior
                row.append("yes" if ok else "no")
        rows.append(row)''', '''            for mg in (0.01, 0.02, 0.03):
                ok = ni[(ni.k == k) & np.isclose(ni.margin, mg)].iloc[0].is_non_inferior
                txt = "yes" if ok else "no"
                row.append(f"\\\\textbf{{{txt}}}" if mg == 0.02 else txt)
            hk = hh[(hh.k == k) & np.isclose(hh.margin, 0.02)].iloc[0]
            row.append(B("yes" if hk.ni_holm else "no"))
        rows.append(row)''')
rep('''    rows = []
    for k in range(16, 0, -1):''', '''    hh = pd.read_csv(S / "h1_holm.csv")
    hh = hh[(hh.analysis == "H1") & np.isclose(hh["lambda"], 0.0)]
    rows = []
    for k in range(16, 0, -1):''')
rep('''"Non-inferior when the lower 95\\\\% bound exceeds $-\\\\delta$; $\\\\delta = 0.02$ is primary.",
          "tab:sparse_ni", "rcccccc",
          "$k$ & Macro-F1 (mean $\\\\pm$ SD) & $\\\\Delta_k$ & 95\\\\% CI & $\\\\delta$=0.01 & "
          "$\\\\delta$=0.02 & $\\\\delta$=0.03", rows)''', '''"Non-inferior when the lower 95\\\\% bound exceeds $-\\\\delta$; $\\\\delta = 0.02$ is primary "
          "(bold). " + B("Holm: non-inferiority at $\\\\delta = 0.02$ after the plan's Holm correction "
          "over the 15 tested $k$, applied post hoc (Supplementary Table~\\\\ref{tab:h1_holm})."),
          "tab:sparse_ni", "rccccccc",
          "$k$ & Macro-F1 (mean $\\\\pm$ SD) & $\\\\Delta_k$ & 95\\\\% CI & $\\\\delta$=0.01 & "
          "\\\\textbf{$\\\\delta$=0.02 (primary)} & $\\\\delta$=0.03 & " + B("Holm (0.02)"), rows)''')
rep('''        f"{d4(r.mean_diff)}, $p$={p(r.p_holm)}" for k in ks''',
    '''        f"{d4(r.mean_diff)}, " + B(f"$p$ {pr(r.p_holm)}") for k in ks''')
rep('''            f"{d4(r.mean_diff)}, $p$={p(r.p_raw)}" for k in ks''',
    '''            f"{d4(r.mean_diff)}, " + B(f"$p$ {pr(r.p_raw)}") for k in ks''')
rep('''same comparison model and training subsample; random removal averages 100 (500 at "''',
    '''same comparison model and training subsample; " + B("Remove-Random") + " averages 100 (500 at "''')
rep('''          "Kept & Top removed & Random & Bottom removed & Top$-$Bottom & Top$-$Random & "
          "Random$-$Bottom", rows)''', '''          B("Retained") + " & " + B("Remove-Top") + " & " + B("Remove-Random") + " & "
          + B("Remove-Bottom") + " & Top$-$Bottom & Top$-$Random & Random$-$Bottom", rows)''')

i = s.index('    db = pd.read_csv(S / "db5_non_inferiority_by_k.csv")')
j = s.index('    return 0\n', i)
s = s[:i] + '''    db = pd.read_csv(S / "db5_non_inferiority_by_k.csv")
    dh = pd.read_csv(S / "h1_holm.csv")
    dh = dh[(dh.analysis == "DB5") & np.isclose(dh.margin, 0.02)].set_index("k")
    rob = pd.read_csv(S / "db5_bootstrap_seed_robustness.csv").set_index("k")
    rows = []
    for k in range(15, 0, -1):
        r = db[(db.k == k) & np.isclose(db.margin, 0.02)].iloc[0]
        rows.append([str(k), f3(r.mean_k), d4(r.mean_diff),
                     B(f"{r.lcb_95:+.6f}".replace("-", "$-$")),
                     "yes" if r.is_non_inferior else "no", B("yes" if dh.loc[k, "ni_holm"] else "no"),
                     f"{100 * rob.loc[k, 'frac_seeds_non_inferior_0.02']:.0f}\\\\%"])
    table("tab_replication",
          B("NinaPro DB5 sparse curve (exploratory; cross-fitted ranking, $\\\\lambda = 0$; 10 subjects; "
            "reference $k = 16$, mean Macro-F1 " + f3(db.mean_ref.iloc[0]) + "; margin $\\\\delta = 0.02$). "
            "LCB to 6 decimals because the $k = 12$ decision lies at the margin. NI = lower bound "
            "above $-\\\\delta$ (primary, uncorrected); Holm = after Holm correction over 15 $k$; "
            "seeds = share of 200 alternative bootstrap seeds under which $k$ is non-inferior."),
          "tab:replication", "rcccccc",
          "$k$ & Macro-F1 & $\\\\Delta_k$ & LCB & NI & Holm & Seeds NI", rows, star=False)

    bp = pd.read_csv(S / "bipolar_non_inferiority_by_k.csv")
    bp = bp[np.isclose(bp["lambda"], 0.0)]
    brob = pd.read_csv(S / "bipolar_bootstrap_seed_robustness.csv").set_index("k")
    rows = []
    for k in range(7, 0, -1):
        b = bp[(bp.k == k) & np.isclose(bp.margin, 0.02)].iloc[0]
        rows.append([str(k), f3(b.mean_k), d4(b.mean_diff), f"{d4(b.lcb_95)} to {d4(b.ucb_95)}",
                     "yes" if b.is_non_inferior else "no",
                     f"{100 * brob.loc[k, 'frac_seeds_non_inferior_0.02']:.0f}\\\\%"])
    table("tab_bipolar",
          B("GRABMyo derived bipolar pairs $F_j - F_{j+8}$ (exploratory; 43 participants; "
            "$\\\\lambda = 0$). Reference = $k = 8$ model of the same curve (200k-window subsample), "
            "mean Macro-F1 " + f3(bp.mean_ref.iloc[0]) + "; margin $\\\\delta = 0.02$."),
          "tab:bipolar", "rccccc",
          "$k$ & Macro-F1 & $\\\\Delta_k$ & 95\\\\% CI & NI & Seeds NI", rows, star=False)

    # H1 with the plan's Holm correction (post hoc) and fixed sequence (post-hoc sensitivity)
    hh = pd.read_csv(S / "h1_holm.csv")
    h = hh[(hh.analysis == "H1") & np.isclose(hh["lambda"], 0.0) & np.isclose(hh.margin, 0.02)]
    rows = [[str(int(r.k)), d4(r.mean_delta), d4(r.lcb95), p(r.p_boot_one_sided), p(r.p_holm),
             "yes" if r.ni_unadjusted else "no", "yes" if r.ni_holm else "no",
             "yes" if r.ni_fixed_sequence_posthoc else "no"]
            for _, r in h.sort_values("k", ascending=False).iterrows()]
    ks = hh[hh.analysis == "H1"].groupby(["lambda", "margin"]).apply(
        lambda g: pd.Series({"u": g.k[g.ni_unadjusted].min(), "h": g.k[g.ni_holm].min(),
                             "f": g.k[g.ni_fixed_sequence_posthoc].min()}), include_groups=False)
    note = "$k^*$ (unadjusted / Holm / fixed sequence) at $\\\\lambda = 0$: " + "; ".join(
        f"$\\\\delta$ = {mg:g}: {int(ks.loc[(0.0, mg), 'u'])} / {int(ks.loc[(0.0, mg), 'h'])} / "
        f"{int(ks.loc[(0.0, mg), 'f'])}" for mg in (0.01, 0.02, 0.03))
    same = all(ks.xs(mg, level="margin").nunique().max() == 1 for mg in (0.01, 0.02, 0.03))
    note += ("; identical for all four $\\\\lambda$." if same
             else "; not identical across $\\\\lambda$ (see artifacts/statistics/h1_holm.csv).")
    table("tab_h1_holm",
          B("H1 with the plan's Holm correction (applied post hoc; 43 participants, $\\\\lambda = 0$, "
            "$\\\\delta = 0.02$). $p$ = one-sided cluster-bootstrap $p$ for $H_0\\\\colon "
            "\\\\bar\\\\Delta_k \\\\le -\\\\delta$ (10,000 resamples); Holm over the 15 tested $k$ at "
            "$\\\\alpha = 0.025$. Fixed sequence (post-hoc sensitivity): $k = 15, 14, \\\\ldots$ tested "
            "in order, stopping at the first failure."),
          "tab:h1_holm", "rccccccc",
          "$k$ & $\\\\bar\\\\Delta_k$ & LCB & $p$ & $p_{\\\\mathrm{Holm}}$ & NI & NI Holm & Fixed seq.",
          rows, star=False, note=B(note))

''' + s[j:]
p.write_text(s, encoding="utf-8")
print("patched 42")
