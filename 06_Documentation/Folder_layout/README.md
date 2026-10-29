# Folder layout and cleanup record

The numbered folders provide the browsing layout for this study:

The cleanup fingerprints below describe the state before the subsequent Figure 1 update and manuscript rebuild. Current publication outputs and their verification are documented separately in the [2026-10-29 study review](../Study_review_20261029/REVIEW.md).

| Folder | Open it for |
| --- | --- |
| [01_Publication](../../01_Publication/) | Existing article, supplement, LaTeX and release ZIP |
| [02_Figures](../../02_Figures/README.md) | Publication plots by figure number and topic, with source data |
| [03_Code](../../03_Code/CODE_INDEX.md) | Scripts grouped by task and Python package modules |
| [04_Results](../../04_Results/) | Tables, participant metrics, rankings and experiments |
| [05_Data](../../05_Data/) | Raw sessions, caches and dataset documentation |
| [06_Documentation](../README.md) | Study reports, reproduction records and author materials |
| [90_Archive](../../90_Archive/) | Earlier manuscripts, invalidated outputs and working records |

## Canonical paths

Windows `.lnk` shortcuts open the original folders in this checkout. The hidden root folders remain the execution and provenance paths. Do not run scripts from copied environment or utility folders expecting them to behave as the canonical project root.

The main publication and figure exports are convenience copies. Their SHA-256 hashes were checked against the originals during this cleanup. The frozen release directories, datasets and research code were preserved.

## Cleanup on 2026-10-29

The project was already arranged into numbered folders. Its 30 existing Windows shortcuts still targeted `F:\grabmyo_data`. They were retargeted to this checkout at `E:\grabmyo_data`. The root and code guides were corrected, a complete code index was added, and the figure index now points to real generator paths and lists the plotted source-data files. Extra shortcuts expose earlier plots and historical root reports from their relevant folders.

This was a navigation cleanup. It did not recompute metrics, regenerate figures, assess study completion, or rerun the scientific publication gate. Some historical executable scripts still contain `F:` paths, as documented in the code guide.

## Records

- [folder_map.csv](folder_map.csv): current shortcut targets and exported-copy sources.
- [organization_state.json](organization_state.json): current layout, copy hashes and original fingerprints.
- [cleanup_20261029_before_hashes.csv](cleanup_20261029_before_hashes.csv): pre-cleanup fingerprints of code, configurations, tests, exports, their originals and release ZIPs.
- [cleanup_20261029_verification.json](cleanup_20261029_verification.json): current verification results and their scope.
- [Before_cleanup_20261029](Before_cleanup_20261029/): previous navigation documents, manifests and shortcuts, preserved with their former paths for rollback.
- [original_root_inventory.csv](original_root_inventory.csv): historical inventory from the first organization; retained as provenance.

Shortcuts are specific to the checkout location. After relocating the project again, use `relative_path` and `relative_target` in `organization_state.json` to rebuild them for the new root. Historical backups deliberately retain the former paths.

[Back to project guide](../../README.md)
