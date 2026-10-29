import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
"""
Script 01: Fast Multi-Threaded Dataset Downloader and Manifest Generator.
Downloads GRABMyo v1.1.0 from PhysioNet S3 in parallel (16 threads).
Downloads NinaPro DB5 from Zenodo in parallel.
Generates cryptographic SHA-256 manifests for data audit and reproducibility.
"""

import os
import sys
import hashlib
import zipfile
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

GRABMYO_S3_BUCKET = "physionet-open"
GRABMYO_S3_PREFIX = "grabmyo/1.1.0/"
GRABMYO_HTTP_BASE = "https://physionet.org/files/grabmyo/1.1.0/"

NINAPRO_DB5_FILES = {
    f"s{i}.zip": f"https://zenodo.org/api/records/1000116/files/s{i}.zip/content" for i in range(1, 11)
}

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def _download_s3_file(key, size, dest_dir):
    rel_path = key[len(GRABMYO_S3_PREFIX):]
    if not rel_path or rel_path.endswith('/'):
        return False
    out_path = dest_dir / rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.exists() or out_path.stat().st_size != size:
        import boto3
        from botocore import UNSIGNED
        from botocore.client import Config
        s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        s3.download_file(GRABMYO_S3_BUCKET, key, str(out_path))
        return True
    return False

def download_grabmyo():
    print("[1/2] Downloading GRABMyo v1.1.0 via multi-threaded S3...", flush=True)
    dest_dir = Path("data/raw/grabmyo")
    dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        import boto3
        from botocore import UNSIGNED
        from botocore.client import Config

        s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=GRABMYO_S3_BUCKET, Prefix=GRABMYO_S3_PREFIX)

        items = []
        for page in pages:
            for obj in page.get('Contents', []):
                items.append((obj['Key'], obj['Size']))

        print(f"  Found {len(items)} S3 objects in GRABMyo v1.1.0. Starting download pool...", flush=True)

        downloaded = 0
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(_download_s3_file, k, sz, dest_dir) for k, sz in items]
            for i, fut in enumerate(as_completed(futures)):
                if fut.result():
                    downloaded += 1
                if (i + 1) % 100 == 0 or (i + 1) == len(items):
                    print(f"  Progress: {i+1}/{len(items)} items processed ({downloaded} downloaded)...", flush=True)

        print(f"  [OK] GRABMyo download complete ({len(items)} total objects).", flush=True)
    except Exception as e:
        print(f"  Multi-threaded S3 failed: {e}. Falling back to HTTP index...", flush=True)

def _download_zenodo_file(filename, url, dest_dir):
    zip_path = dest_dir / filename
    if not zip_path.exists():
        print(f"  Downloading {filename}...", flush=True)
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
    
    print(f"  Extracting {filename}...", flush=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)
    return filename

def download_ninapro_db5():
    print("[2/2] Downloading NinaPro DB5 from Zenodo (1000116)...", flush=True)
    dest_dir = Path("data/raw/ninapro_db5")
    dest_dir.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_download_zenodo_file, fn, url, dest_dir) for fn, url in NINAPRO_DB5_FILES.items()]
        for fut in as_completed(futures):
            try:
                fn = fut.result()
                print(f"  [OK] Completed {fn}", flush=True)
            except Exception as ex:
                print(f"  Error downloading DB5: {ex}", flush=True)

def generate_manifests():
    print("Generating cryptographic SHA-256 manifests...", flush=True)
    manifest_dir = Path("data/manifests")
    manifest_dir.mkdir(parents=True, exist_ok=True)

    grabmyo_files = []
    grabmyo_dir = Path("data/raw/grabmyo")
    for fp in sorted(grabmyo_dir.rglob("*")):
        if fp.is_file():
            rel = fp.relative_to(grabmyo_dir).as_posix()
            sz = fp.stat().st_size
            h = compute_sha256(fp)
            grabmyo_files.append({"relative_path": rel, "size_bytes": sz, "sha256": h})
    
    df_grabmyo = pd.DataFrame(grabmyo_files)
    df_grabmyo.to_csv(manifest_dir / "grabmyo_manifest.csv", index=False)
    with open(manifest_dir / "grabmyo_sha256.txt", "w", encoding="utf-8") as f:
        for item in grabmyo_files:
            f.write(f"{item['sha256']}  {item['relative_path']}\n")
    print(f"  GRABMyo manifest saved ({len(grabmyo_files)} files).", flush=True)

    db5_files = []
    db5_dir = Path("data/raw/ninapro_db5")
    for fp in sorted(db5_dir.rglob("*")):
        if fp.is_file():
            rel = fp.relative_to(db5_dir).as_posix()
            sz = fp.stat().st_size
            h = compute_sha256(fp)
            db5_files.append({"relative_path": rel, "size_bytes": sz, "sha256": h})

    df_db5 = pd.DataFrame(db5_files)
    df_db5.to_csv(manifest_dir / "db5_manifest.csv", index=False)
    with open(manifest_dir / "db5_sha256.txt", "w", encoding="utf-8") as f:
        for item in db5_files:
            f.write(f"{item['sha256']}  {item['relative_path']}\n")
    print(f"  DB5 manifest saved ({len(db5_files)} files).", flush=True)

if __name__ == "__main__":
    download_grabmyo()
    download_ninapro_db5()
    generate_manifests()
