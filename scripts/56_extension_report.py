"""Generate extension text/tables from complete verified participant results only."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'artifacts/participant_attribution'


def main():
    comparisons = pd.read_csv(OUT / 'paired_comparisons.csv')
    ni = pd.read_csv(OUT / 'non_inferiority.csv')
    curve = pd.read_csv(OUT / 'sparse_curve.csv')
    penalty = pd.read_csv(OUT / 'penalty_gate.csv')
    benefit = int(penalty.supports_penalty_benefit.sum())
    harm = int(penalty.supports_penalty_harm.sum())
    diagnostics=[]
    for method,path in [('fold',ROOT/'artifacts/rankings/cross_fitted_scores.csv'),
                        ('participant',OUT/'scores.csv')]:
        scores=pd.read_csv(path)
        diagnostics.append({'aggregation':method,'outer_participants':scores.outer_participant.nunique(),
                            'median_relative_mad':float((scores.U_instability/scores.A_central).median())})
    pd.DataFrame(diagnostics).to_csv(OUT/'aggregation_diagnostics.csv',index=False)
    changed = comparisons[comparisons.n_tied < 43]
    significant = comparisons[comparisons.p_holm < .05]
    better = significant[significant.mean_diff > 0]
    worse = significant[significant.mean_diff < 0]
    rows=[]
    for lam in (0.,.25,.5,1.):
        n = ni[(ni['lambda']==lam) & np.isclose(ni.margin,.02)]
        k = n[n.ni_unadjusted].k.min()
        kh = n[n.ni_holm].k.min()
        c = comparisons[(comparisons['lambda']==lam) & (comparisons.k==12)].iloc[0]
        rows.append({'lambda':lam,'kstar_unadjusted':k,'kstar_holm':kh,
                     'delta_at_12':c.mean_diff,'lcb95':c.lcb95,'ucb95':c.ucb95,'p_holm':c.p_holm})
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT/'report_summary.csv',index=False)
    as_k=lambda k:'none' if pd.isna(k) else str(int(k))
    def count_phrase(n, total):
        return 'none' if n == 0 else f'{n} of {total}'
    text = (r'\paragraph{Participant-level attribution extension (post hoc)} \chg{'
        f'All {curve.participant_id.nunique()} outer participants were evaluated under both aggregations. '
        'The median relative dispersion of attribution ($U_c/A_c$ over all outer-fold and electrode cells) '
        f'increased from {100*diagnostics[0]["median_relative_mad"]:.2f}\\% under fold aggregation to '
        f'{100*diagnostics[1]["median_relative_mad"]:.2f}\\% under participant aggregation; these cells are '
        'not independent replicates, so this change is descriptive. '
        f'Participant and fold aggregation were compared at every penalty and reduced subset size '
        f'({len(comparisons)} comparisons); in {len(changed)} of them at least one participant'
        "'s score differed between the two aggregations. After Holm correction across these comparisons, "
        f'{count_phrase(len(better), len(comparisons))} favoured participant aggregation and '
        f'{count_phrase(len(worse), len(comparisons))} favoured fold aggregation. '
        'Results for every penalty are given in supplementary table~S7; no penalty was selected using '
        'outer-test performance. These comparisons test the change of aggregation and do not replace the '
        'original H3 result. Within participant aggregation, each positive penalty was also compared with '
        f'attribution magnitude alone ({len(penalty)} Holm-corrected comparisons): '
        f'{count_phrase(benefit, len(penalty))} favoured the penalty and '
        f'{count_phrase(harm, len(penalty))} favoured magnitude alone.}}\n')
    generated = ROOT/'manuscript/generated'
    generated.mkdir(exist_ok=True)
    (generated/'participant_extension_results.tex').write_text(text,encoding='utf-8')
    if benefit:
        abstract = ('A post-hoc participant-level aggregation supported penalty benefits in '
                    'some multiplicity-adjusted comparisons; all candidates remain exploratory. ')
    elif harm:
        abstract = ('A post-hoc participant-level aggregation found no corrected penalty benefit '
                    'and detected harm in some comparisons. ')
    else:
        abstract = ('A post-hoc participant-level aggregation also found no statistically '
                    'detectable penalty benefit. ')
    (generated/'participant_extension_abstract.tex').write_text(abstract+'\n',encoding='utf-8')
    discussion = ('The participant-level extension directly measures between-person attribution '
                  'heterogeneity instead of averaging it within inner folds. ')
    if benefit:
        discussion += ('It produced evidence of penalty benefit in some corrected comparisons, '
                       'but this post-hoc result needs validation in a new cohort before replacing '
                       'the original protocol. ')
    else:
        discussion += ('This targeted change did not establish a corrected predictive benefit '
                       'from the penalty. Greater sensitivity to attribution heterogeneity does '
                       'not by itself make a ranking more useful for reduced-array prediction. ')
    if harm:
        discussion += ('Some corrected comparisons favoured magnitude alone, so penalising '
                       'heterogeneity can also remove useful predictive information. ')
    discussion += ('The complete comparison grid is reported to avoid choosing an aggregation '
                   'or penalty from outer-test outcomes.\n')
    (generated/'participant_extension_discussion.tex').write_text(discussion,encoding='utf-8')
    lines=[r'\begin{table}[htbp]',r'\centering',r'\small',
        r'\caption{Participant-level attribution extension (post hoc; GRABMyo, 43 participants). \chg{$k^*$: smallest non-inferior subset against the 16-electrode model of the same curve (200,000-window training sample; margin 0.02), without and with Holm correction. $\Delta$ at $k = 12$: mean paired difference, participant minus fold aggregation, at the same penalty, with 95\% participant cluster-bootstrap confidence interval; $p_{\rm Holm}$: Wilcoxon signed-rank, Holm-corrected across all penalties and subset sizes.}}',
        r'\label{tab:participant_extension}',r'\begin{tabular}{rrrrr}',r'\toprule',
        r'$\lambda$ & $k^*$ & $k^*$ (Holm) & $\Delta$ at $k=12$ (95\% CI) & $p_{\rm Holm}$ \\',r'\midrule']
    for _,r in summary.iterrows():
        p = '$<0.001$' if r.p_holm < .001 else f'{r.p_holm:.3f}'
        lines.append(f"{r['lambda']:g} & {as_k(r.kstar_unadjusted)} & {as_k(r.kstar_holm)} & "
                     f"{r.delta_at_12:+.4f} ({r.lcb95:+.4f}, {r.ucb95:+.4f}) & {p} \\\\")
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (ROOT/'manuscript/tables/tab_participant_extension.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    gestures=pd.read_csv(ROOT/'artifacts/prediction_audit/gesture_summary.csv')
    gestures=gestures[gestures.model=='M_XGBoost'].sort_values('gesture_id')
    if len(gestures)!=16 or not (gestures.n_participants==43).all():
        raise ValueError('per-gesture result cohort incomplete')
    # gesture names in the order stated by the dataset's MotionSequence.txt ("ordered ... from 1 to 17")
    names=['Lateral prehension','Thumb adduction','Thumb and little finger opposition',
           'Thumb and index finger opposition','Thumb and index finger extension',
           'Thumb and little finger extension','Index and middle finger extension',
           'Little finger extension','Index finger extension','Thumb finger extension','Wrist extension',
           'Wrist flexion','Forearm supination','Forearm pronation','Hand open','Hand close']
    lines=[r'\begin{table}[htbp]',r'\centering',r'\small',
        r'\caption{{Full-array XGBoost F1 score by active GRABMyo gesture (43 participants). Mean F1 across participants with a 95\% percentile cluster-bootstrap confidence interval of the mean (10,000 resamples). Gesture names follow the order given in the dataset file MotionSequence.txt.}}',
        r'\label{tab:gesture_audit}',r'\begin{tabular}{rlrr}',r'\toprule',
        r'ID & Gesture & Mean F1 & 95\% bootstrap CI \\',r'\midrule']
    for _,r in gestures.iterrows():
        lines.append(f'{int(r.gesture_id)} & {names[int(r.gesture_id)-1]} & {r.mean_f1:.3f} & {r.lcb95:.3f} to {r.ucb95:.3f} \\\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (ROOT/'manuscript/tables/tab_gesture_audit.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    provenance = [{'output':'participant_extension_results.tex','source':'artifacts/participant_attribution/paired_comparisons.csv',
                   'derivation':'counts of all comparisons, any changed person, positive/negative mean difference with p_holm < 0.05'},
                  {'output':'tab_participant_extension.tex','source':'artifacts/participant_attribution/report_summary.csv',
                   'derivation':'all four penalties; smallest passing reduced k, paired k12 difference and interval'}]
    provenance.append({'output':'participant_extension_results.tex','source':'artifacts/participant_attribution/penalty_gate.csv',
                       'derivation':'counts of benefit and harm under the complete corrected penalty family'})
    for output in ('participant_extension_abstract.tex','participant_extension_discussion.tex'):
        provenance.append({'output':output,'source':'artifacts/participant_attribution/penalty_gate.csv',
                           'derivation':'conditional interpretation from corrected benefit and harm flags; all candidates retained'})
    provenance.append({'output':'participant_extension_results.tex','source':'artifacts/participant_attribution/aggregation_diagnostics.csv',
                       'derivation':'descriptive median of U/A across validated outer-fold/electrode cells, not inferential sample size'})
    provenance.append({'output':'tab_gesture_audit.tex','source':'artifacts/prediction_audit/gesture_summary.csv',
                       'derivation':'participant-level F1 for each active gesture, reconstructed from saved predictions'})
    pd.DataFrame(provenance).to_csv(generated/'extension_provenance.csv',index=False)
    report=['# Participant-level attribution extension','',
            'Status: complete, exploratory. It does not retrospectively replace frozen H3.','',
            f'Holm-significant comparisons favouring participant aggregation: {len(better)}; favouring fold aggregation: {len(worse)}.', '',
            'The complete result tables and input SHA256 fingerprints are in `artifacts/participant_attribution/`.']
    (ROOT/'reports/participant_attribution_extension.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    matrix=comparisons.pivot(index='lambda',columns='k',values='mean_diff').sort_index()
    bound=max(float(abs(matrix.to_numpy()).max()),1e-5)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42})
    fig,ax=plt.subplots(figsize=(7.1,2.2))
    cmap=LinearSegmentedColormap.from_list('difference',['#d55e00','#ffffff','#0072b2'])
    im=ax.imshow(matrix.to_numpy(),cmap=cmap,vmin=-bound,vmax=bound,aspect='auto')
    ax.set_xticks(range(len(matrix.columns)),[str(k) for k in matrix.columns])
    ax.set_yticks(range(len(matrix.index)),[f'{lam:g}' for lam in matrix.index])
    ax.set_xlabel('electrodes retained, k');ax.set_ylabel('penalty, lambda')
    for i,lam in enumerate(matrix.index):
        for j,k in enumerate(matrix.columns):
            r=comparisons[(comparisons['lambda']==lam)&(comparisons.k==k)].iloc[0]
            if r.p_holm<.05:
                ax.text(j,i,'*',ha='center',va='center',color='black')
    cb=fig.colorbar(im,ax=ax,pad=.02)
    cb.set_label('Mean Macro-F1 difference')
    fig.tight_layout()
    for ext in ('pdf','png'):
        fig.savefig(ROOT/f'manuscript/figures/fig9_participant_extension.{ext}',dpi=250,bbox_inches='tight')
    plt.close(fig)
    PAGE_WIDTH = 153 / 25.4  # iopjournal.cls text width in inches (~6.02 in)
    fig,axes=plt.subplots(1,3,figsize=(PAGE_WIDTH,2.5),sharex=True,sharey=True)
    letters = ["a", "b", "c"]
    for ax,lam,let in zip(axes,(.25,.5,1.),letters):
        subset=penalty[penalty['lambda']==lam].sort_values('k')
        ax.axvline(0,color='#777777',lw=.8,ls='--')
        for y,(_,r) in enumerate(subset.iterrows()):
            colour='#0072b2' if r.mean_diff>=0 else '#d55e00'
            ax.plot([r.lcb95,r.ucb95],[y,y],color=colour,lw=1.6)
            ax.plot(r.mean_diff,y,'o',color=colour,markersize=3.5)
            if r.p_holm<.05:
                ax.annotate('*',(r.mean_diff,y),xytext=(0,4),textcoords='offset points',ha='center',fontsize=9)
        ax.set_title(let, loc='left', fontsize=10, fontweight='bold')
        ax.set_title(rf'$\lambda = {lam:g}$', loc='center', fontsize=8.5)
        ax.set_yticks(range(len(subset)),[f'$k = {int(k)}$' for k in subset.k], fontsize=8.5)
        ax.tick_params(axis='y',length=0)
        ax.grid(axis='x',alpha=.2)
        ax.spines[['top','right','left']].set_visible(False)
    axes[0].invert_yaxis()
    axes[0].set_xlim(-0.015, 0.018)
    fig.supxlabel('Mean paired Macro-F1 difference: penalty minus magnitude alone',fontsize=8.5)
    fig.tight_layout()
    for ext in ('pdf','png'):
        fig.savefig(ROOT/f'manuscript/figures/fig10_penalty_gate.{ext}',dpi=250,bbox_inches='tight')
    plt.close(fig)
    print('Generated extension results, table and provenance from complete participant results.')


if __name__=='__main__':
    main()
