# GRABMyo electrode-selection study

The [GitHub repository](https://github.com/taminhtri2003/Sensor-Selection) contains code, figures, manuscripts, results and verification records. Downloaded datasets, feature caches and local environments are excluded; see [repository contents and restoration notes](06_Documentation/GITHUB_CONTENTS.md).

Start with the numbered folders below. Open the figure guide to find a plot by topic, or the code index to find a script by task.

- [Figure guide](02_Figures/README.md): Figures 1-6 and S1-S7 in PDF, SVG and PNG.
- [Code guide](03_Code/README.md) and [complete code index](03_Code/CODE_INDEX.md): analysis, plotting, checks and manuscript scripts.
- [Main article](01_Publication/Main_article.pdf) and [supplement](01_Publication/Supplementary_material.pdf): current review copies recompiled on 2026-10-29, with the updated Figure 1.
- [Whole-study review](06_Documentation/Study_review_20261029/REVIEW.md): fresh numerical verification, design limitations and Figure 1 corrections required before submission.

| Folder | Contents |
| --- | --- |
| [01_Publication](01_Publication/) | Main article, supplementary article, editable LaTeX, data and complete publication ZIP |
| [02_Figures](02_Figures/) | All 13 figures in PDF, SVG and PNG, with source data and a figure guide |
| [03_Code](03_Code/) | Analysis scripts, Python package, configurations, tests, environment files and dataset utilities |
| [04_Results](04_Results/) | Publication tables, complete statistics, participant results, rankings and experiments |
| [05_Data](05_Data/) | Raw GRABMyo sessions, downloaded datasets, caches, metadata and dataset documentation |
| [06_Documentation](06_Documentation/) | Study reports, reproducibility instructions, literature and author information |
| [90_Archive](90_Archive/) | Older manuscripts, previous packages, historical reports and working records |

The numbered folders are the browsing layout. Windows folder shortcuts open the canonical code, results and data in this checkout (`E:\grabmyo_data`). These working locations remain in place because scripts and dataset manifests depend on them; earlier root folders are hidden in the normal Windows Explorer view. Enable **View > Show > Hidden items** to inspect them directly.

Use the root `scripts/` and `src/` paths for execution. Environment files and dataset utilities in `03_Code/` are reference copies. Some historical scripts contain absolute paths to the former `F:` drive; see the [code guide](03_Code/README.md) before rebuilding outputs.

The [folder map and cleanup record](06_Documentation/Folder_layout/README.md) explain where everything lives. No experiments were rerun as part of the folder cleanup.

Institutional ethics determination, funding, conflicts, contributions and the public archive link still require author confirmation. They are recorded separately under `06_Documentation/Author_materials/author_declarations.md`.
