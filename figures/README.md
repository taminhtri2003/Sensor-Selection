# Figure guide

PDF is for publication, SVG for vector editing where available, and PNG for quick viewing. The [Source_data](Source_data/) folder contains the plotted numerical data.

Figure 1 is the author-supplied PDF updated on 2026-10-29, with a matching PNG preview. Its native editable SVG was not supplied; the previous SVG/PNG are preserved in the review backup. The new artwork reverses the documented ring labels and includes a 3 cm separation inconsistent with the documented 2 cm montage. It remains a review draft pending correction. Figures 2-6 and S1-S7 retain their earlier result-driven exports.

The [figure index](figure_index.csv) lists each format, its generation script and its source-data files. These are the existing publication exports; earlier and exploratory plots remain in `artifacts/figures/` and in the Git history.

| Figure | Purpose | PDF | SVG | PNG |
| --- | --- | --- | --- | --- |
| 1 | Recording and selection overview (review draft) | [PDF](PDF/fig1_montage.pdf) | Author source needed | [PNG](PNG/fig1_montage.png) |
| 2 | Participant-disjoint cross-fitting | [PDF](PDF/fig2_crossfit.pdf) | [SVG](SVG/fig2_crossfit.svg) | [PNG](PNG/fig2_crossfit.png) |
| 3 | Electrode count and participant losses | [PDF](PDF/fig3_noninferiority.pdf) | [SVG](SVG/fig3_noninferiority.svg) | [PNG](PNG/fig3_noninferiority.png) |
| 4 | Selection-strategy comparisons | [PDF](PDF/fig4_selection_utility.pdf) | [SVG](SVG/fig4_selection_utility.svg) | [PNG](PNG/fig4_selection_utility.png) |
| 5 | Gesture losses and attribution | [PDF](PDF/fig5_task_and_attribution.pdf) | [SVG](SVG/fig5_task_and_attribution.svg) | [PNG](PNG/fig5_task_and_attribution.png) |
| 6 | Limits of transfer | [PDF](PDF/fig6_generalization_limits.pdf) | [SVG](SVG/fig6_generalization_limits.svg) | [PNG](PNG/fig6_generalization_limits.png) |
| S1 | Rest and window-length sensitivity | [PDF](PDF/figS1_sensitivity_curves.pdf) | [SVG](SVG/figS1_sensitivity_curves.svg) | [PNG](PNG/figS1_sensitivity_curves.png) |
| S2 | Changes in gesture confusion | [PDF](PDF/figS2_confusion_change.pdf) | [SVG](SVG/figS2_confusion_change.svg) | [PNG](PNG/figS2_confusion_change.png) |
| S3 | Full-array classifier comparison | [PDF](PDF/figS3_classifier_context.pdf) | [SVG](SVG/figS3_classifier_context.svg) | [PNG](PNG/figS3_classifier_context.png) |
| S4 | Participant versus fold aggregation | [PDF](PDF/figS4_participant_aggregation.pdf) | [SVG](SVG/figS4_participant_aggregation.svg) | [PNG](PNG/figS4_participant_aggregation.png) |
| S5 | Full-array session transfer | [PDF](PDF/figS5_cross_session.pdf) | [SVG](SVG/figS5_cross_session.svg) | [PNG](PNG/figS5_cross_session.png) |
| S6 | Attribution heterogeneity | [PDF](PDF/figS6_attribution_heterogeneity.pdf) | [SVG](SVG/figS6_attribution_heterogeneity.svg) | [PNG](PNG/figS6_attribution_heterogeneity.png) |
| S7 | Complete geometric reduction curve | [PDF](PDF/figS7_geometric_count_curve.pdf) | [SVG](SVG/figS7_geometric_count_curve.svg) | [PNG](PNG/figS7_geometric_count_curve.png) |

Figure-generation script for the result-driven figures: [67_revision_figures.py](../scripts/67_revision_figures.py). This script generates the previous montage schematic for Figure 1; it does not recreate the new author artwork. The executable source used for the earlier exports is preserved in [the frozen analysis snapshot](../manuscript_revision/20261014/reproducibility/code/scripts/67_revision_figures.py). Run scripts from the project root. Regeneration writes to the dated scientific record; it is unnecessary for viewing an export.

[Publication files](../publication/README.md) | [Back to project guide](../README.md)
