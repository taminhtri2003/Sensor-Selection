"""Verify local GRABMyo files against the dataset-provided SHA256SUMS.txt.

This is the integrity check the prior run claimed to have performed but never did.
Writes data/manifests/grabmyo_integrity.csv and reports/grabmyo_integrity.md.
Exit code is non-zero if any file is missing or mismatched.
"""

import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRABMYO = ROOT / "data" / "grabmyo"
SUMS = GRABMYO / "SHA256SUMS.txt"
OUT_CSV = ROOT / "data" / "manifests" / "grabmyo_integrity.csv"
OUT_MD = ROOT / "reports" / "grabmyo_integrity.md"
CHUNK = 1 << 20


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(CHUNK)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def main():
    if not SUMS.exists():
        print(f"FATAL: {SUMS} not found", flush=True)
        return 2

    entries = []
    with open(SUMS, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            expected, _, rel = line.partition(" ")
            rel = rel.strip().lstrip("*")
            if expected and rel:
                entries.append((expected, rel))

    print(f"manifest entries: {len(entries)}", flush=True)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    n_ok = n_missing = n_bad = 0
    rows = []

    for i, (expected, rel) in enumerate(entries, 1):
        path = GRABMYO / rel
        if not path.exists():
            status, actual, size = "MISSING", "", ""
            n_missing += 1
        else:
            actual = sha256(path)
            size = path.stat().st_size
            if actual == expected:
                status = "OK"
                n_ok += 1
            else:
                status = "MISMATCH"
                n_bad += 1
        rows.append({
            "path": rel,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "size_bytes": size,
            "status": status,
        })
        if i % 2000 == 0:
            print(f"  {i}/{len(entries)}  ok={n_ok} missing={n_missing} bad={n_bad}", flush=True)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["path", "expected_sha256", "actual_sha256", "size_bytes", "status"]
        )
        w.writeheader()
        w.writerows(rows)

    verdict = "PASS" if (n_missing == 0 and n_bad == 0) else "FAIL"
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as fh:
        fh.write("# GRABMyo v1.1.0 raw-data integrity verification\n\n")
        fh.write("Verified against the dataset-provided `SHA256SUMS.txt`.\n\n")
        fh.write(f"- Manifest entries: **{len(entries)}**\n")
        fh.write(f"- Verified OK: **{n_ok}**\n")
        fh.write(f"- Missing: **{n_missing}**\n")
        fh.write(f"- Checksum mismatch: **{n_bad}**\n\n")
        fh.write(f"**Verdict: {verdict}**\n\n")
        if n_missing or n_bad:
            fh.write("## Failing files\n\n")
            for r in rows:
                if r["status"] != "OK":
                    fh.write(f"- `{r['path']}` — {r['status']}\n")
        fh.write("\nPer-file detail: `data/manifests/grabmyo_integrity.csv`\n")

    print(f"\n{verdict}: ok={n_ok} missing={n_missing} mismatch={n_bad}", flush=True)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
