"""Fit generated tables to the IOP single-column text width (153 mm): tighter column spacing,
an adjustbox cap at \\textwidth, and two-line 'difference / p' cells in the baselines table."""
from pathlib import Path

p = Path(__file__).resolve().parents[2] / "scripts" / "42_generate_tables.py"
s = p.read_text(encoding="utf-8")

old = r'''             f"\\begin{{tabular}}{{{colspec}}}", "\\toprule", header + " \\\\", "\\midrule"]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}"]'''
new = r'''             "\\setlength{\\tabcolsep}{4pt}", "\\begin{adjustbox}{max width=\\textwidth}",
             f"\\begin{{tabular}}{{{colspec}}}", "\\toprule", header + " \\\\", "\\midrule"]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{adjustbox}"]'''
assert old in s, "table body not found"
s = s.replace(old, new)

old = r'''        f"{d4(r.mean_diff)}, " + B(f"$p$ {pr(r.p_holm)}") for k in ks'''
new = r'''        "\\makecell{" + d4(r.mean_diff) + " \\\\ " + B(f"$p$ {pr(r.p_holm)}") + "}" for k in ks'''
assert old in s
s = s.replace(old, new)
old = r'''            f"{d4(r.mean_diff)}, " + B(f"$p$ {pr(r.p_raw)}") for k in ks'''
new = r'''            "\\makecell{" + d4(r.mean_diff) + " \\\\ " + B(f"$p$ {pr(r.p_raw)}") + "}" for k in ks'''
assert old in s
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("patched")
