"""Audit every DOI in docs/literature/literature_matrix.csv against Crossref (arXiv for arXiv ids).

A DOI that returns 404, or resolves to a record whose title does not match the recorded citation,
is flagged. Writes reports/literature_doi_audit.csv. Nothing is corrected automatically: a flagged
row must be re-verified by hand or removed before the matrix is cited.
"""
import difflib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "literature-audit (mailto:tri.tm2003@gmail.com)"}


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", str(s).lower())


def fetch(doi):
    for attempt in range(3):
        try:
            req = urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi),
                                         headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=30))["message"], None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, "404"
            err = str(e)
        except Exception as e:                                   # noqa: BLE001
            err = str(e)
        time.sleep(2 * (attempt + 1))
    return None, err


def main():
    lm = pd.read_csv(ROOT / "docs" / "literature" / "literature_matrix.csv")
    rows = []
    for _, r in lm.iterrows():
        ref = str(r.get("doi_or_url", ""))
        m = re.search(r"(10\.\d{4,9}/[^\s,;]+)", ref)
        rec = {"study_id": r["study_id"], "citation": str(r["citation"])[:120], "doi_or_url": ref}
        if not m:
            rec["status"] = "NO_DOI"
        else:
            doi = m.group(1).rstrip(".")
            msg, err = fetch(doi)
            if msg is None:
                rec["status"] = "DOI_NOT_FOUND" if err == "404" else f"LOOKUP_ERROR {err}"
            else:
                title = (msg.get("title") or [""])[0]
                rec["crossref_title"] = title
                rec["crossref_year"] = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
                rec["crossref_first_author"] = (msg.get("author") or [{}])[0].get("family", "")
                # the recorded citation string should contain (most of) the true title
                cit = norm(r["citation"])
                t = norm(title)
                sm = difflib.SequenceMatcher(None, t, cit)
                match = sum(b.size for b in sm.get_matching_blocks()) / max(len(t), 1)
                rec["title_match"] = round(match, 2)
                rec["status"] = "OK" if match >= 0.85 else "TITLE_MISMATCH"
            time.sleep(0.3)
        rows.append(rec)
        print(f"{rec['study_id']:>6} {rec['status']:16s} {rec.get('title_match', '')!s:5s} "
              f"{rec['citation'][:70]}", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "reports" / "literature_doi_audit.csv", index=False)
    print("\n", out.status.value_counts().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
