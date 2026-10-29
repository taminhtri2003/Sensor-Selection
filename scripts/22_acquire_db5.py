"""Acquire and integrity-check NinaPro DB5 from the official Zenodo record (1000116).

The prior run created data/raw/ninapro_db5/ and left it empty, then reported DB5 replication
results anyway. This script downloads the data, verifies it against the checksums Zenodo
publishes, extracts it, and structurally validates every .mat file.

Any file failing verification is quarantined to data/quarantine/db5/ with a recorded reason and
re-downloaded once. Nothing corrupt is silently used.

Outputs:
  data/raw/ninapro_db5/            extracted subject folders
  data/manifests/db5_manifest.csv  sha256 + zenodo md5 per archive
  reports/db5_integrity.csv        per-.mat structural validation
  reports/db5_integrity.md
"""

import csv
import hashlib
import json
import shutil
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import scipy.io as sio

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ninapro_db5"
QUARANTINE = ROOT / "data" / "quarantine" / "db5"
MANIFESTS = ROOT / "data" / "manifests"
REPORTS = ROOT / "reports"
RECORD = "https://zenodo.org/api/records/1000116"

EXPECTED_SUBJECTS = 10
EXPECTED_EMG_CH = 16
EXPECTED_FS = 200.0


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def fetch_record():
    with urllib.request.urlopen(RECORD, timeout=90) as r:
        return json.load(r)


def download(url, dest, retries=5):
    """Fetch to a .part file then rename, retrying on the transient TLS read timeouts Zenodo
    throws on larger archives. A partial transfer is discarded rather than left to masquerade
    as a complete file."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    last = None
    for attempt in range(1, retries + 1):
        try:
            if tmp.exists():
                tmp.unlink()
            req = urllib.request.Request(url, headers={"User-Agent": "grabmyo-study/1.0"})
            with urllib.request.urlopen(req, timeout=180) as r, open(tmp, "wb") as fh:
                shutil.copyfileobj(r, fh, length=1 << 20)
            tmp.replace(dest)
            return dest
        except Exception as exc:
            last = exc
            wait = min(30, 3 * attempt)
            print(f"    retry {attempt}/{retries} after {type(exc).__name__}: {exc} "
                  f"(waiting {wait}s)", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"download failed after {retries} attempts: {last}")


def acquire():
    RAW.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    QUARANTINE.mkdir(parents=True, exist_ok=True)

    rec = fetch_record()
    files = {f["key"]: f for f in rec.get("files", [])}
    print(f"zenodo record lists {len(files)} files", flush=True)

    manifest = []
    for key in sorted(files, key=lambda k: int("".join(c for c in k if c.isdigit()) or 0)):
        meta = files[key]
        expected_md5 = (meta.get("checksum") or "").replace("md5:", "")
        url = meta["links"]["self"]
        dest = RAW / key

        for attempt in (1, 2):
            if not dest.exists():
                print(f"  downloading {key} ({meta['size']/1e6:.1f} MB) attempt {attempt}", flush=True)
                download(url, dest)
            got_md5 = md5(dest)
            if not expected_md5 or got_md5 == expected_md5:
                break
            print(f"  [BAD] {key} md5 {got_md5} != {expected_md5}; quarantining", flush=True)
            shutil.move(str(dest), str(QUARANTINE / f"{key}.attempt{attempt}"))

        got_md5 = md5(dest) if dest.exists() else ""
        ok = bool(dest.exists()) and (not expected_md5 or got_md5 == expected_md5)
        manifest.append({
            "file": key, "size_bytes": dest.stat().st_size if dest.exists() else 0,
            "zenodo_md5": expected_md5, "local_md5": got_md5,
            "sha256": sha256(dest) if dest.exists() else "",
            "checksum_ok": ok,
        })
        print(f"  {key}: {'OK' if ok else 'FAILED'}", flush=True)

    with open(MANIFESTS / "db5_manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    return manifest


def extract():
    for zp in sorted(RAW.glob("*.zip")):
        try:
            with zipfile.ZipFile(zp) as z:
                bad = z.testzip()
                if bad is not None:
                    print(f"  [BAD ARCHIVE] {zp.name}: corrupt member {bad}", flush=True)
                    shutil.move(str(zp), str(QUARANTINE / zp.name))
                    continue
                z.extractall(RAW)
            print(f"  extracted {zp.name}", flush=True)
        except zipfile.BadZipFile as e:
            print(f"  [BAD ARCHIVE] {zp.name}: {e}", flush=True)
            shutil.move(str(zp), str(QUARANTINE / zp.name))


def validate():
    rows = []
    for mat in sorted(RAW.rglob("*.mat")):
        row = {
            "path": str(mat.relative_to(ROOT)).replace("\\", "/"),
            "size_bytes": mat.stat().st_size, "sha256": sha256(mat),
            "load_success": False, "n_samples": 0, "n_emg_channels": 0, "fs": "",
            "stimulus_present": False, "restimulus_present": False,
            "repetition_present": False, "rerepetition_present": False,
            "n_movements": 0, "finite": False, "corruption_flag": "", "reason": "",
        }
        try:
            d = sio.loadmat(str(mat))
            row["load_success"] = True
            emg = d.get("emg")
            if emg is None:
                row.update(corruption_flag="NO_EMG", reason="no 'emg' variable")
                rows.append(row)
                continue
            emg = np.asarray(emg)
            row["n_samples"], row["n_emg_channels"] = int(emg.shape[0]), int(emg.shape[1])
            row["finite"] = bool(np.all(np.isfinite(emg)))
            row["stimulus_present"] = "stimulus" in d
            row["restimulus_present"] = "restimulus" in d
            row["repetition_present"] = "repetition" in d
            row["rerepetition_present"] = "rerepetition" in d
            if "restimulus" in d:
                row["n_movements"] = int(len(np.unique(np.asarray(d["restimulus"]))))
            elif "stimulus" in d:
                row["n_movements"] = int(len(np.unique(np.asarray(d["stimulus"]))))
            if "frequency" in d:
                row["fs"] = float(np.asarray(d["frequency"]).ravel()[0])

            problems = []
            if row["n_emg_channels"] != EXPECTED_EMG_CH:
                problems.append(f"{row['n_emg_channels']} EMG channels != {EXPECTED_EMG_CH}")
            if row["n_samples"] < 1000:
                problems.append(f"only {row['n_samples']} samples")
            if not row["finite"]:
                problems.append("non-finite values")
            if not row["stimulus_present"]:
                problems.append("no stimulus")
            row["corruption_flag"] = "OK" if not problems else "STRUCTURE"
            row["reason"] = "; ".join(problems)
        except Exception as exc:
            row.update(corruption_flag="LOAD_ERROR", reason=f"{type(exc).__name__}: {exc}")
        rows.append(row)

    if rows:
        with open(REPORTS / "db5_integrity.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    return rows


def main():
    manifest = acquire()
    print("\nextracting...", flush=True)
    extract()
    print("\nvalidating .mat files...", flush=True)
    rows = validate()

    n_ok = sum(1 for r in rows if r["corruption_flag"] == "OK")
    subjects = sorted({Path(r["path"]).parent.name for r in rows})
    chan = sorted({r["n_emg_channels"] for r in rows})
    fss = sorted({r["fs"] for r in rows if r["fs"] != ""})

    with open(REPORTS / "db5_integrity.md", "w", encoding="utf-8") as f:
        f.write("# NinaPro DB5 acquisition and integrity check\n\n")
        f.write(f"Source: Zenodo record 1000116 (official NinaPro DB5 distribution).\n\n")
        f.write("## Archives\n\n| file | size (MB) | md5 matches Zenodo |\n|---|---|---|\n")
        for m in manifest:
            f.write(f"| {m['file']} | {m['size_bytes']/1e6:.1f} | {m['checksum_ok']} |\n")
        f.write(f"\n## Extracted .mat files\n\n")
        f.write(f"- Files validated: **{len(rows)}**\n")
        f.write(f"- Structurally OK: **{n_ok}**\n")
        f.write(f"- Subject folders: **{len(subjects)}** {subjects}\n")
        f.write(f"- EMG channel counts observed: {chan}\n")
        f.write(f"- Sampling rates observed: {fss}\n\n")
        bad = [r for r in rows if r["corruption_flag"] != "OK"]
        if bad:
            f.write("## Failures\n\n")
            for r in bad:
                f.write(f"- `{r['path']}` — {r['corruption_flag']}: {r['reason']}\n")
        f.write("\nPer-file detail: `reports/db5_integrity.csv`, "
                "archive checksums: `data/manifests/db5_manifest.csv`\n")

    print(f"\narchives ok: {sum(1 for m in manifest if m['checksum_ok'])}/{len(manifest)}")
    print(f"mat files: {len(rows)}  structurally ok: {n_ok}")
    print(f"subjects: {len(subjects)}  channels: {chan}  fs: {fss}")

    all_ok = all(m["checksum_ok"] for m in manifest) and n_ok == len(rows) and len(rows) > 0
    print("\nDB5 INTEGRITY: " + ("PASS" if all_ok else "FAIL"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
