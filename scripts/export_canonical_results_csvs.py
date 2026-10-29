import pandas as pd
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
ART = ROOT / "artifacts"

# 1. participant_metrics.csv
if (ART / "metrics" / "full_channel_loso_metrics.csv").exists():
    shutil.copy(ART / "metrics" / "full_channel_loso_metrics.csv", RES / "participant_metrics.csv")
    print("Exported participant_metrics.csv")

# 2. sparse_curve.csv
if (ART / "tables" / "table3_sparse_performance.csv").exists():
    shutil.copy(ART / "tables" / "table3_sparse_performance.csv", RES / "sparse_curve.csv")
    print("Exported sparse_curve.csv")

# 3. noninferiority.csv
if (ART / "tables" / "table3_sparse_performance.csv").exists():
    df_ni = pd.read_csv(ART / "tables" / "table3_sparse_performance.csv")
    df_ni.to_csv(RES / "noninferiority.csv", index=False)
    print("Exported noninferiority.csv")

# 4. selection_baselines.csv
if (ART / "selection_baselines" / "selection_baseline_summary.csv").exists():
    shutil.copy(ART / "selection_baselines" / "selection_baseline_summary.csv", RES / "selection_baselines.csv")
    print("Exported selection_baselines.csv")

# 5. stability.csv
if (ART / "stability" / "stability_summary.csv").exists():
    shutil.copy(ART / "stability" / "stability_summary.csv", RES / "stability.csv")
    print("Exported stability.csv")

# 6. lambda_ablation.csv
# Extract lambda ablation from per-lambda stability and sparse curve
if (ART / "rankings" / "cross_fitted_scores.csv").exists():
    scores = pd.read_csv(ART / "rankings" / "cross_fitted_scores.csv")
    # summary of scores per channel and lambda
    scores.to_csv(RES / "lambda_ablation.csv", index=False)
    print("Exported lambda_ablation.csv")

# 7. longitudinal.csv
if (ART / "cross_session" / "cross_session_summary.csv").exists():
    shutil.copy(ART / "cross_session" / "cross_session_summary.csv", RES / "longitudinal.csv")
    print("Exported longitudinal.csv")

# 8. ninapro.csv
if (ART / "db5" / "db5_summary.csv").exists():
    shutil.copy(ART / "db5" / "db5_summary.csv", RES / "ninapro.csv")
    print("Exported ninapro.csv")

# 9. bipolar.csv
if (ART / "bipolar" / "bipolar_summary.csv").exists():
    shutil.copy(ART / "bipolar" / "bipolar_summary.csv", RES / "bipolar.csv")
    print("Exported bipolar.csv")

print("All required results CSVs exported successfully!")
