# Downloading the study datasets

The study uses two public datasets. Neither is stored in this repository.

| Dataset | Version | Size | Licence | Goes to |
| --- | --- | --- | --- | --- |
| [GRABMyo](https://physionet.org/content/grabmyo/1.1.0/) | 1.1.0 | 9.8 GB ZIP, 30,715 files | CC BY 4.0 | `data/grabmyo/` |
| [NinaPro DB5](https://zenodo.org/records/1000116) | Zenodo record 1000116 | 10 ZIPs, about 200 MB | CC BY-ND 4.0 | `data/raw/ninapro_db5/` |

Run every command from the repository root. You need about 20 GB of free disk for GRABMyo if you use the ZIP route (archive plus extracted files) and about 1 GB for DB5.

## Tools

`aria2c` opens several connections per file and resumes broken transfers, which makes it the fastest simple option here.

```bash
# Debian/Ubuntu
sudo apt-get install -y aria2 unzip
# or, without root, inside the conda environment
conda install -c conda-forge aria2
```

## 1. GRABMyo 1.1.0

PhysioNet serves the full-project ZIP from its public AWS bucket, which supports byte ranges. Sixteen parallel connections are usually much faster than a browser or `wget`.

```bash
mkdir -p data/grabmyo
aria2c -x 16 -s 16 -k 64M --file-allocation=none --continue=true \
  --max-tries=0 --retry-wait=5 \
  -d data/grabmyo -o grabmyo-1.1.0.zip \
  https://physionet-open.s3.amazonaws.com/grabmyo/grabmyo-1.1.0.zip

# The archive has one top-level folder; move its contents into data/grabmyo/.
unzip -q data/grabmyo/grabmyo-1.1.0.zip -d data/grabmyo/
mv data/grabmyo/gesture-recognition-and-biometrics-electromyogram-grabmyo-1.1.0/* data/grabmyo/
rmdir data/grabmyo/gesture-recognition-and-biometrics-electromyogram-grabmyo-1.1.0
rm data/grabmyo/grabmyo-1.1.0.zip
```

Moving the archive contents overwrites the copies of `RECORDS`, `SHA256SUMS.txt`, `subject-info.csv` and the other dataset documents tracked in `data/grabmyo/`. They are the same files.

If the download stops, run the same `aria2c` command again; it continues from where it stopped.

### Alternative: individual files, no ZIP

This needs no extra disk for the archive. With 30,715 small files, a client that runs many requests at once is the fast choice. [s5cmd](https://github.com/peak/s5cmd/releases) is a single binary:

```bash
s5cmd --no-sign-request --numworkers 128 \
  cp 's3://physionet-open/grabmyo/1.1.0/*' data/grabmyo/
```

With the AWS CLI instead:

```bash
aws configure set default.s3.max_concurrent_requests 64
aws s3 sync --no-sign-request s3://physionet-open/grabmyo/1.1.0/ data/grabmyo/
```

### Verify

The dataset ships SHA-256 checksums for every file. The study script checks all of them and writes `data/manifests/grabmyo_integrity.csv` and `reports/grabmyo_integrity.md`:

```bash
python scripts/audit_grabmyo_integrity.py
```

It must report 30,715 entries, all OK. For a faster check that runs on many cores and writes nothing:

```bash
cd data/grabmyo
awk '{print $1"  "$2}' SHA256SUMS.txt > /tmp/grabmyo.sha256
split -n l/16 /tmp/grabmyo.sha256 /tmp/grabmyo_sums.
ls /tmp/grabmyo_sums.* | xargs -P 16 -I{} sha256sum -c --quiet {}
rm /tmp/grabmyo.sha256 /tmp/grabmyo_sums.*; cd ../..
```

No output means every file matched.

Expected layout:

```text
data/grabmyo/
├── Session1/  Session2/  Session3/     WFDB records (.dat/.hea)
├── RECORDS  SHA256SUMS.txt  subject-info.csv  MotionSequence.txt
├── readme.txt  LICENSE.txt  DeviceInfo.pdf  Electrodelocation.pdf  GestureList.JPG
└── grabmyo_*.py  *.m                    dataset tools
```

## 2. NinaPro DB5

Zenodo limits each connection, so download the ten archives in parallel with a few connections each. aria2c checks the MD5 that Zenodo publishes for each file.

```bash
mkdir -p data/raw/ninapro_db5
cat > /tmp/db5.aria2 <<'EOF'
https://zenodo.org/records/1000116/files/s1.zip?download=1
  out=s1.zip
  checksum=md5=bb63c22179b4a750bac2499aecd72021
https://zenodo.org/records/1000116/files/s2.zip?download=1
  out=s2.zip
  checksum=md5=9d91c5a524123e950cd7cab3b42887ae
https://zenodo.org/records/1000116/files/s3.zip?download=1
  out=s3.zip
  checksum=md5=700d15737cd5219cf9e9a0370670f246
https://zenodo.org/records/1000116/files/s4.zip?download=1
  out=s4.zip
  checksum=md5=0eac484016793b28481d786a0f73e270
https://zenodo.org/records/1000116/files/s5.zip?download=1
  out=s5.zip
  checksum=md5=0ff40dd987a67f5b2770671504fc9b23
https://zenodo.org/records/1000116/files/s6.zip?download=1
  out=s6.zip
  checksum=md5=850e853dd6dfd0170fa38189509133d1
https://zenodo.org/records/1000116/files/s7.zip?download=1
  out=s7.zip
  checksum=md5=e55ee99af5fb924a6a8d8500752b6d78
https://zenodo.org/records/1000116/files/s8.zip?download=1
  out=s8.zip
  checksum=md5=281c62eade1ffd58579b57aa36df579d
https://zenodo.org/records/1000116/files/s9.zip?download=1
  out=s9.zip
  checksum=md5=622e562482f5b9c9b10d6cfe7b3d1636
https://zenodo.org/records/1000116/files/s10.zip?download=1
  out=s10.zip
  checksum=md5=765d22dbe4241c67f3b6dbacf79fc901
EOF
aria2c -i /tmp/db5.aria2 -d data/raw/ninapro_db5 -j 10 -x 4 -s 4 \
  --continue=true --max-tries=0 --retry-wait=5 --file-allocation=none
```

The MD5 values above were read from the Zenodo API (`https://zenodo.org/api/records/1000116`) on 2026-10-30.

Then let the study's own acquisition step check, extract and validate the archives. It finds the ZIPs already in place, checks them again against Zenodo, downloads only missing or corrupt ones, extracts them and checks every `.mat` file:

```bash
python scripts/22_acquire_db5.py
```

It writes `data/manifests/db5_manifest.csv` and `reports/db5_integrity.md`. A complete download gives 10 participants, 30 `.mat` files and 16 EMG channels at 200 Hz.

## Speed notes

- Throughput depends mostly on the route between you and the server. In Asia, the AWS bucket (`us-east-1`) is often faster with more connections; raise `-x`/`-s` to 16 and `--numworkers` to 256 if the link is not saturated.
- PhysioNet and Zenodo may slow or refuse clients that open too many connections. If you see HTTP 429 or 503, lower `-x` and `-j` and run the same command again; finished parts are kept.
- Put the data on a local SSD, not a network mount. Extracting and hashing 30,715 files is limited by disk speed.
