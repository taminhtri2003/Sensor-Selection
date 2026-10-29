import pandas as pd
import numpy as np
from scipy.stats import wilcoxon

df = pd.read_csv('artifacts/faithfulness/deletion_curves.csv')

# Unique n_kept values that have all three arms
# Check which n_kept have all three arms
counts = df.groupby(['n_kept', 'arm']).size().unstack()
print("Counts by n_kept and arm:")
print(counts)

results = []
rng = np.random.default_rng(20260728)

for k in [4, 6, 8, 12]:
    sub = df[df.n_kept == k]
    p_top = sub[sub.arm == 'remove_top'].set_index('participant_id')['macro_f1']
    p_rnd = sub[sub.arm == 'remove_random'].set_index('participant_id')['macro_f1']
    p_bot = sub[sub.arm == 'remove_bottom'].set_index('participant_id')['macro_f1']
    
    # Common participants
    common = p_top.index.intersection(p_rnd.index).intersection(p_bot.index)
    
    y_top = p_top.loc[common].values
    y_rnd = p_rnd.loc[common].values
    y_bot = p_bot.loc[common].values
    
    # Means and SDs
    m_top, s_top = np.mean(y_top), np.std(y_top, ddof=1)
    m_rnd, s_rnd = np.mean(y_rnd), np.std(y_rnd, ddof=1)
    m_bot, s_bot = np.mean(y_bot), np.std(y_bot, ddof=1)
    
    # Paired differences
    # Definition of faithfulness: remove_top < remove_random < remove_bottom
    # So (remove_top - remove_bottom) should be negative and significant
    # (remove_top - remove_random) should be negative
    # (remove_random - remove_bottom) should be negative
    diff_top_bot = y_top - y_bot
    diff_top_rnd = y_top - y_rnd
    diff_rnd_bot = y_rnd - y_bot
    
    def boot_ci(diff_vals):
        b = np.array([np.mean(rng.choice(diff_vals, size=len(diff_vals), replace=True)) for _ in range(10000)])
        return np.percentile(b, 2.5), np.percentile(b, 97.5)
    
    lcb_tb, ucb_tb = boot_ci(diff_top_bot)
    lcb_tr, ucb_tr = boot_ci(diff_top_rnd)
    lcb_rb, ucb_rb = boot_ci(diff_rnd_bot)
    
    w_tb = wilcoxon(diff_top_bot)
    w_tr = wilcoxon(diff_top_rnd)
    w_rb = wilcoxon(diff_rnd_bot)
    
    # Rank biserial correlation
    # r = 1 - 2*W / (n*(n+1)/2) where W is min of ranks or rank sum
    def rank_biserial(diff_vals):
        pos = diff_vals[diff_vals > 0]
        neg = diff_vals[diff_vals < 0]
        # Using standard formula: (sum(ranks_pos) - sum(ranks_neg)) / total_rank_sum
        from scipy.stats import rankdata
        ranks = rankdata(np.abs(diff_vals[diff_vals != 0]))
        r_pos = np.sum(ranks[diff_vals[diff_vals != 0] > 0])
        r_neg = np.sum(ranks[diff_vals[diff_vals != 0] < 0])
        return (r_pos - r_neg) / (r_pos + r_neg) if (r_pos + r_neg) > 0 else 0.0

    rb_tb = rank_biserial(diff_top_bot)
    rb_tr = rank_biserial(diff_top_rnd)
    rb_rb = rank_biserial(diff_rnd_bot)
    
    results.append({
        'n_kept': k,
        'mean_top': m_top, 'sd_top': s_top,
        'mean_rnd': m_rnd, 'sd_rnd': s_rnd,
        'mean_bot': m_bot, 'sd_bot': s_bot,
        'diff_top_bot': np.mean(diff_top_bot), 'lcb_tb': lcb_tb, 'ucb_tb': ucb_tb, 'p_tb': w_tb.pvalue, 'rb_tb': rb_tb,
        'diff_top_rnd': np.mean(diff_top_rnd), 'lcb_tr': lcb_tr, 'ucb_tr': ucb_tr, 'p_tr': w_tr.pvalue, 'rb_tr': rb_tr,
        'diff_rnd_bot': np.mean(diff_rnd_bot), 'lcb_rb': lcb_rb, 'ucb_rb': ucb_rb, 'p_rb': w_rb.pvalue, 'rb_rb': rb_rb,
    })

res_df = pd.DataFrame(results)

# Holm correction across the 4 tests for each comparison family
from statsmodels.stats.multitest import multipletests
res_df['p_tb_holm'] = multipletests(res_df['p_tb'], method='holm')[1]
res_df['p_tr_holm'] = multipletests(res_df['p_tr'], method='holm')[1]
res_df['p_rb_holm'] = multipletests(res_df['p_rb'], method='holm')[1]

print("\n--- ROAR FAITHFULNESS AUDIT TABLE ---")
for idx, r in res_df.iterrows():
    print(f"\nRetained Channels k = {int(r['n_kept'])} (Removed: {16 - int(r['n_kept'])}):")
    print(f"  Top:    {r['mean_top']:.4f} +/- {r['sd_top']:.4f}")
    print(f"  Random: {r['mean_rnd']:.4f} +/- {r['sd_rnd']:.4f}")
    print(f"  Bottom: {r['mean_bot']:.4f} +/- {r['sd_bot']:.4f}")
    print(f"  Top vs Bottom: diff = {r['diff_top_bot']:+.4f} (95% CI [{r['lcb_tb']:+.4f}, {r['ucb_tb']:+.4f}]), p = {r['p_tb']:.4e}, p_holm = {r['p_tb_holm']:.4e}, rank-biserial = {r['rb_tb']:.3f}")
    print(f"  Top vs Random: diff = {r['diff_top_rnd']:+.4f} (95% CI [{r['lcb_tr']:+.4f}, {r['ucb_tr']:+.4f}]), p = {r['p_tr']:.4e}, p_holm = {r['p_tr_holm']:.4e}, rank-biserial = {r['rb_tr']:.3f}")
    print(f"  Random vs Bot: diff = {r['diff_rnd_bot']:+.4f} (95% CI [{r['lcb_rb']:+.4f}, {r['ucb_rb']:+.4f}]), p = {r['p_rb']:.4e}, p_holm = {r['p_rb_holm']:.4e}, rank-biserial = {r['rb_rb']:.3f}")

res_df.to_csv('results/roar.csv', index=False)
print("\nSaved exact ROAR metrics to results/roar.csv")
