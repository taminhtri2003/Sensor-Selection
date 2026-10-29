import pandas as pd
import numpy as np

sparse = pd.read_csv('artifacts/bipolar/bipolar_sparse_curve.csv')
full = pd.read_csv('artifacts/bipolar/bipolar_full_channel_metrics.csv')

print('Full bipolar 8 pairs baseline Macro-F1:', full['macro_f1'].mean())

for lam in [0.0, 0.25, 0.5, 1.0]:
    print(f"\n--- Bipolar Lambda = {lam} ---")
    df_lam = sparse[sparse['lambda'] == lam]
    for k in range(8, 0, -1):
        df_k = df_lam[df_lam.channels_k == k]
        merged = pd.merge(df_k, full[['participant_id', 'macro_f1']], on='participant_id', suffixes=('_k', '_full'))
        diff = merged['macro_f1_k'] - merged['macro_f1_full']
        rng = np.random.default_rng(20260728)
        boot_diffs = np.array([np.mean(rng.choice(diff, size=len(diff), replace=True)) for _ in range(10000)])
        lcb = np.percentile(boot_diffs, 2.5)
        ucb = np.percentile(boot_diffs, 97.5)
        ni = lcb > -0.020
        print(f"k={k}: mean_k={merged['macro_f1_k'].mean():.4f} +/- {merged['macro_f1_k'].std(ddof=1):.4f}, diff={diff.mean():+.4f}, LCB={lcb:+.4f}, UCB={ucb:+.4f}, Non-Inferior={ni}")
