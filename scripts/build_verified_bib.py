"""Build manuscript/references.bib from verified identifiers only.

Every journal/conference entry is generated from its Crossref record (so author lists, year,
venue, volume and pages are the registry's, not typed by hand). The three machine-learning
conference papers without DOIs are generated from their arXiv records. The previous bib, which
contained DOIs that do not exist or resolve to unrelated papers, is archived.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "bib-builder (mailto:tri.tm2003@gmail.com)"}

DOIS = {
    "pradhan2022multiday": "10.1038/s41597-022-01836-y",
    "pizzolato2017comparison": "10.1371/journal.pone.0186132",
    "kaczmarek2019putemg": "10.3390/s19163548",
    "goldberger2000physionet": "10.1161/01.CIR.101.23.e215",
    "farina2004extraction": "10.1152/japplphysiol.01070.2003",
    "farina2014extraction": "10.1109/TNSRE.2014.2305111",
    "vujaklija2016new": "10.2147/ORR.S71468",
    "cote2019deep": "10.1109/TNSRE.2019.2896269",
    "stango2015spatial": "10.1109/TNSRE.2014.2366752",
    "muceli2014extracting": "10.1109/TNSRE.2013.2282898",
    "smith2011determining": "10.1109/TNSRE.2010.2100828",
    "farrell2007optimal": "10.1109/TNSRE.2007.891391",
    "phinyomark2012feature": "10.1016/j.eswa.2012.01.102",
    "phinyomark2018emg": "10.3390/bdcc2030021",
    "qu2021reduce": "10.1155/2021/9929684",
    "liu2014emg": "10.1016/j.medengphy.2014.04.003",
    "altimemy2013classification": "10.1109/JBHI.2013.2249590",
    "li2010quantifying": "10.1109/TNSRE.2009.2039619",
    "hargrove2006effect": "10.1109/IEMBS.2006.4397877",
    "kaufmann2010fluctuating": "10.1109/IEMBS.2010.5627288",
    "vidovic2016improving": "10.1109/TNSRE.2015.2492619",
    "scheme2011electromyogram": "10.1682/JRRD.2010.09.0177",
    "englehart2003robust": "10.1109/TBME.2003.813539",
    "hudgins1993new": "10.1109/10.204774",
    "lundberg2020local": "10.1038/s42256-019-0138-9",
    "visani2022statistical": "10.1080/01605682.2020.1865846",
    "samek2017evaluating": "10.1109/TNNLS.2016.2599820",
    "meinshausen2010stability": "10.1111/j.1467-9868.2010.00740.x",
    "schuirmann1987comparison": "10.1007/BF01068419",
    "walker2011understanding": "10.1007/s11606-010-1513-8",
}
DATACITE = {
    "jiang2024grabmyo": "10.13026/89dm-f662",
}

ARXIV = {
    "lundberg2017unified": ("1705.07874", "Advances in Neural Information Processing Systems", "30", "2017"),
    "hooker2019benchmark": ("1806.10758", "Advances in Neural Information Processing Systems", "32", "2019"),
    "sundararajan2017axiomatic": ("1703.01365", "Proceedings of the 34th International Conference on Machine Learning, PMLR", "70", "2017"),
}
PREPRINTS = {   # arXiv preprints (not peer-reviewed at time of citation)
    "xiang2026roshap": "2605.15154",
    "salmi2025shapaad": "2507.03814",
    "kelodjou2023shaping": "2312.12115",
    "campbell2018noninferiority": "1807.03413",
}


def tex_escape(s):
    s = re.sub(r"<[^>]+>", "", s).replace("&amp;", "&").replace("&", "\\&")
    return s.replace("%", "\\%").replace("_", "\\_")


def crossref(doi):
    req = urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi), headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=30))["message"]


def cached_entries():
    """Entries of the previous generated bib, keyed by citation key. Used only when the arXiv API
    refuses a request (it returned HTTP 406 on 2026-09-21); those entries were themselves
    generated from arXiv records by an earlier run of this script."""
    p = ROOT / "manuscript" / "references.bib"
    if not p.exists():
        return {}
    blocks = re.split(r"\n(?=@)", p.read_text(encoding="utf-8"))
    return {re.match(r"@\w+\{([^,]+),", b).group(1): b.strip() for b in blocks if b.startswith("@")}


def arxiv_query(aid, timeout):
    req = urllib.request.Request(f"https://export.arxiv.org/api/query?id_list={aid}", headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode()


def main():
    cache = cached_entries()
    entries = []
    for key, doi in DOIS.items():
        m = crossref(doi)
        authors = " and ".join(f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
                               for a in m.get("author", []))
        year = (m.get("published-print") or m.get("issued"))["date-parts"][0][0]
        kind = "inproceedings" if m["type"] == "proceedings-article" else "article"
        venue_field = "booktitle" if kind == "inproceedings" else "journal"
        fields = {
            "author": authors, "title": "{" + tex_escape(m["title"][0]) + "}",
            venue_field: tex_escape((m.get("container-title") or [""])[0]), "year": str(year),
            "volume": m.get("volume", ""), "number": m.get("issue", ""),
            "pages": m.get("page", "").replace("-", "--"), "doi": m["DOI"],
        }
        body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items() if v)
        entries.append(f"@{kind}{{{key},\n{body}\n}}")
        print(f"{key:28s} {year} {m['title'][0][:70]}")
        time.sleep(0.3)
    for key, (aid, venue, vol, year) in ARXIV.items():
        try:
            x = arxiv_query(aid, 30)
        except urllib.error.HTTPError:
            if key not in cache:
                raise
            entries.append(cache[key])
            print(f"{key:28s} (arXiv API refused; reused previously generated entry)")
            continue
        title = " ".join(re.findall(r"<title>(.*?)</title>", x, re.S)[1].split())
        names = re.findall(r"<name>(.*?)</name>", x)
        authors = " and ".join(f"{n.split()[-1]}, {' '.join(n.split()[:-1])}" for n in names)
        entries.append(f"@inproceedings{{{key},\n  author = {{{authors}}},\n  title = {{{{{title}}}}},\n"
                       f"  booktitle = {{{venue}}},\n  volume = {{{vol}}},\n  year = {{{year}}},\n"
                       f"  eprint = {{{aid}}},\n  archivePrefix = {{arXiv}}\n}}")
        print(f"{key:28s} {year} {title[:70]}")
    for key, aid in PREPRINTS.items():
        time.sleep(4)
        try:
            x = arxiv_query(aid, 40)
        except urllib.error.HTTPError:
            if key not in cache:
                raise
            entries.append(cache[key])
            print(f"{key:28s} (arXiv API refused; reused previously generated entry)")
            continue
        title = " ".join(re.findall(r"<title>(.*?)</title>", x, re.S)[1].split())
        names = re.findall(r"<name>(.*?)</name>", x)
        year = re.findall(r"<published>(\d{4})", x)[0]
        authors = " and ".join(f"{n.split()[-1]}, {' '.join(n.split()[:-1])}" for n in names)
        entries.append(f"@misc{{{key},\n  author = {{{authors}}},\n  title = {{{{{title}}}}},\n"
                       f"  year = {{{year}}},\n  howpublished = {{arXiv preprint arXiv:{aid}}},\n"
                       f"  eprint = {{{aid}}},\n  archivePrefix = {{arXiv}}\n}}")
        print(f"{key:28s} {year} {title[:70]}")
    # datasets with DataCite DOIs (added 2026-09-22; citation requested by PhysioNet)
    for key, doi in DATACITE.items():
        req = urllib.request.Request("https://api.datacite.org/dois/" + doi, headers=UA)
        a = json.load(urllib.request.urlopen(req, timeout=30))["data"]["attributes"]
        authors = " and ".join(c["name"] for c in a["creators"])
        ver = f" (version {a['version']})" if a.get("version") else ""
        entries.append(f"@misc{{{key},\n  author = {{{authors}}},\n"
                       f"  title = {{{{{tex_escape(a['titles'][0]['title'])}{ver}}}}},\n"
                       f"  howpublished = {{{a['publisher']}}},\n  year = {{{a['publicationYear']}}},\n"
                       f"  doi = {{{doi}}}\n}}")
        print(f"{key:28s} {a['publicationYear']} {a['titles'][0]['title'][:70]}")
    out = ROOT / "manuscript" / "references.bib"
    out.write_text("% Generated by scripts/build_verified_bib.py from Crossref / arXiv records.\n"
                   "% Do not add entries by hand: add a verified identifier to the script.\n\n"
                   + "\n\n".join(entries) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
