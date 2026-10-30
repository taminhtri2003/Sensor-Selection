# GRABMyo electrode-selection study

Code, results and manuscript for a study of how few forearm EMG electrodes are needed for gesture recognition on [GRABMyo 1.1.0](https://physionet.org/content/grabmyo/1.1.0/), with a replication on [NinaPro DB5](https://zenodo.org/records/1000116). Analyses use leave-one-participant-out evaluation, and all statistics are computed per participant (N = 43).

- [Main article](publication/Main_article.pdf) and [supplement](publication/Supplementary_material.pdf): current review draft, recompiled 2026-10-29.
- [Whole-study review](docs/Study_review_20261029/REVIEW.md): fresh numerical verification, design limitations and the Figure 1 corrections needed before submission.
- [Downloading the datasets](docs/DATA_DOWNLOAD.md) and [reproducing the study](docs/REPRODUCE.md).

## Layout

| Path | Contents |
| --- | --- |
| [src/](src/) | `semg_sparse` package: features, models, statistics, checkpoints, execution safety |
| [scripts/](scripts/) | Numbered pipeline scripts, audits and manuscript builders |
| [tests/](tests/) | Regression tests (`python -m pytest`) |
| [configs/](configs/) | Statistical analysis configuration |
| [data/](data/) | `grabmyo/`: dataset documents, checksums and tools (raw sessions go here, not in Git); `manifests/`, `metadata/` |
| [artifacts/](artifacts/) | Result files: metrics, rankings, predictions, statistics |
| [publication/](publication/) | Article, supplement, LaTeX source, supplementary data |
| [figures/](figures/) | Figures 1–6 and S1–S7 in PDF, SVG and PNG, with source data |
| [manuscript/](manuscript/) | Manuscript build used by the pipeline scripts |
| [manuscript_revision/](manuscript_revision/20261014/) | Frozen 2026-10-14 revision: reports, reproducibility snapshot |
| [docs/](docs/) | Reports, reproduction and download guides, literature, author materials |
| [reports/](reports/), [audit/](audit/), [runs/](runs/) | Analysis reports, audits and run logs, including the [2026-10-29 rerun](reports/rerun_20261029/STATUS.md) |
| [reproducibility/](reproducibility/) | Recorded execution environments |

Raw recordings, feature caches and local environments are not in the repository; see [docs/GITHUB_CONTENTS.md](docs/GITHUB_CONTENTS.md). Superseded folders removed on 2026-10-30 remain in the Git history.

## Quick start

```bash
conda create -n sensor-selection python=3.10 pip
conda activate sensor-selection
python -m pip install -r reproducibility/requirements_execution_20260922.txt
# download the data: docs/DATA_DOWNLOAD.md
python scripts/audit_grabmyo_integrity.py
make test
make verify
```

Research-integrity rules for contributors and agents are in [AGENTS.md](AGENTS.md). Author declarations (ethics, funding, conflicts, contributions) still need confirmation; see [docs/Author_materials/](docs/Author_materials/).

[LICENSE.txt](LICENSE.txt) is the GRABMyo dataset licence (CC BY 4.0), copied from the dataset. The repository has no separate code licence.
