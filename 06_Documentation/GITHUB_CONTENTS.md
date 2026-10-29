# GitHub repository contents

Destination: https://github.com/taminhtri2003/Sensor-Selection

The repository includes the analysis code, configurations, tests, manuscript sources and PDFs, figures, participant-level result tables, saved predictions, public dataset documentation/manifests, and study review/audit records. Earlier and invalidated research records remain identified as historical material; their presence is not an endorsement of their conclusions.

Downloaded raw recordings, processed signals, feature caches and label/index arrays remain local. This applies to duplicated datasets in historical/frozen folders too. The frozen `manuscript_revision/grabmyo_revision_20261014.zip` and its checksum file are excluded because the archive embeds feature and label arrays; its expanded code, results and documentation are included subject to the same exclusions. Other retained ZIP files are inspected for embedded dataset files before pushing.

Local Python environments, fallback dependencies, credentials, tool settings, scratch directories and disposable TeX auxiliary files are also ignored. Dataset exclusion rules are in the root [.gitignore](../.gitignore). Saved experimental prediction files under `artifacts/predictions/` and revision experiment folders are analysis outputs, not downloaded datasets, and are retained for score reconstruction.

The root [.gitattributes](../.gitattributes) disables automatic line-ending normalization. Existing source and artifact fingerprints depend on exact bytes; Git should preserve the original line endings instead of rewriting them on another operating system.

The numbered folders are the browsing layout. Windows `.lnk` files are local convenience shortcuts; GitHub readers should follow the relative Markdown links in the guides. Reproduction requires separately restoring the public datasets and excluded caches at their documented canonical locations. Some historical scripts retain workstation-specific paths; see the [code guide](../03_Code/README.md).

The current article is a review draft. Its updated Figure 1 needs label/distance corrections, and the study has disclosed development-exposure and author-declaration limitations. See the [whole-study review](Study_review_20261029/REVIEW.md).
