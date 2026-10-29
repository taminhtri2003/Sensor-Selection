from pathlib import Path
import shutil,re,json,hashlib,subprocess,csv
ROOT=Path('F:/grabmyo_data')
OLD=ROOT/'manuscript_revision/20261014'
OUT=ROOT/'manuscript_final/20261016'
SRC=OUT/'manuscript'
OUT.mkdir(parents=True,exist_ok=True)
for p in (OLD/'manuscript').rglob('*'):
    if p.is_file() and p.suffix in {'.tex','.bib','.cls'} or p.name=='orcid.pdf':
        q=SRC/p.relative_to(OLD/'manuscript');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
for p in (OLD/'figures/vector').glob('*.pdf'):
    q=OUT/'figures/vector'/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
# Separate author-only materials from the reader-facing paper.
private=ROOT/'manuscript_final/author_materials/20261016';private.mkdir(parents=True,exist_ok=True)
(private/'author_declarations.md').write_text('''# Author declarations awaiting confirmation

- Institutional determination or exemption for this secondary analysis remains unresolved, as requested. Public dataset status does not establish an exemption.
- Confirm funding and grants, acknowledgements, conflicts of interest and author-approved CRediT contributions.
- Supply a permanent public archive URL or DOI.
- Confirm retained author names, affiliations and correspondence details.

These declarations were deferred by the author. They are omitted from the clean reader-facing manuscript until confirmed; no declaration has been invented.
''',encoding='utf-8')
(private/'reproducibility_settings.json').write_text(json.dumps({'model_random_seed':20260728,'bootstrap_random_seed':20260728,'bootstrap_resamples':10000,'fixed_layout_monte_carlo_repetitions':200,'fixed_layout_generator_seed':20260728,'complete_executable_record':'manuscript_revision/20261014/reproducibility'},indent=2),encoding='utf-8')

def edit(rel,pairs):
    p=SRC/rel;s=p.read_text(encoding='utf-8')
    for a,b in pairs:
        assert a in s,(rel,a[:100]);s=s.replace(a,b)
    p.write_text(s,encoding='utf-8')

def replace_between(s,a,b,new):
    i=s.index(a);j=s.index(b,i);return s[:i]+new+'\n\n'+s[j:]

edit('main.tex',[
(r'\newcommand{\rev}[1]{#1}\newcommand{\chg}[1]{#1}',''),
('Exploratory checks included','Exploratory analyses included'),
('Attribution outperformed mean random subsets in the lighter comparison.','Attribution outperformed mean random subsets with the reduced-budget classifier.'),
])
p=SRC/'main.tex';s=p.read_text(encoding='utf-8');s=replace_between(s,r'\ack{',r'\bibliographystyle',r'''\data{Public GRABMyo v1.1.0 recordings are available from PhysioNet (\url{https://doi.org/10.13026/89dm-f662}); NinaPro DB5 recordings are available from \url{https://ninapro.hevs.ch}.}
\suppdata{The Supplementary contains signal-processing and inference details, exploratory analyses, complete result tables and additional figures.}''');p.write_text(s,encoding='utf-8')
edit('sections/introduction.tex',[
('an internally documented, predefined engineering margin','a specified engineering margin'),
('New exploratory checks use','Exploratory analyses use'),
('without implying a verified absolute anatomical angle','without assigning an absolute anatomical angle'),
])
edit('sections/methods.tex',[
('Historically, the monopolar threshold ($10^{-2}$ mV) was derived from 54 unfiltered records from six participants before LOSO. It was not estimated separately within each outer fold. Subsequent exclusion checks reproduced the identical rounded threshold in all \\LOOMonoFolds\\ folds. Thus the stored features are invariant to this particular exclusion, but the original development sequence should not be described as fully isolated.',r'The monopolar threshold ($10^{-2}$ mV) was calibrated from 54 unfiltered records from six participants before participant partitioning. Excluding each participant left the rounded threshold unchanged in all \LOOMonoFolds\ folds. Threshold calibration therefore involved pooled development data, although its value was invariant to participant exclusion.'),
(r'Filtering was effectively \RevDBFiveBandLow--\RevDBFiveBandHigh\ Hz without a notch; the requested \RevDBFiveBandRequestedHigh\ Hz upper limit was clipped by the shared implementation to $0.45f_s-1$ Hz. Complete raw reconstruction of all saved DB5 feature rows verified this implemented cutoff; the earlier 95 Hz description was a reporting error.',r'Filtering used an effective passband of \RevDBFiveBandLow--\RevDBFiveBandHigh\ Hz without a notch.'),
(' [AUTHOR INPUT REQUIRED: institutional determination or exemption for this secondary analysis remains unresolved.]',''),
(' and fixed seed 20260728',''),
('Training budgets differ across historical tracks:','Training budgets differ across comparisons:'),
('The internally dated analysis plan followed an earlier pilot; no independent registration or Git commit authenticating its date is available. These development exposures qualify claims of wholly prospective evaluation.','The analysis design followed pilot work and was not independently preregistered. This development exposure limits prospective interpretation.'),
('historical threshold pooling','pooled threshold calibration'),
('All penalties and counts are evaluated under the unchanged primary protocol. Exact matching participant/subset fits may be reused with source-row provenance; new subsets require new fits. A historical source-hash mismatch is preserved in the audit, and current reporting uses an isolated refit with current input fingerprints. After observing the penalty results, a descriptive audit compared selected physical site sets and Jaccard similarity at every fixed penalty and count. It added no model fits or inferential tests and did not choose a penalty.','All penalties and counts are evaluated under the primary protocol. A post-hoc descriptive analysis compared selected physical site sets and Jaccard similarity at every fixed penalty and count. It assesses whether penalties change the physical inputs and does not select a penalty.'),
('The historical decision rule requires','The primary decision rule requires'),
(' with seed 20260728',''),
('The original Holm procedure used','The percentile-tail Holm procedure uses'),
('We preserve it and additionally report an exploratory, null-centred studentized bootstrap','An exploratory sensitivity uses a null-centred studentized bootstrap'),
(' No seed or margin is chosen from results.',''),
('The detailed historical secondary families were specified after their underlying results became available and are labeled secondary rather than prospectively confirmatory.','The secondary test families are post-hoc and are not prospectively confirmatory.'),
('Historical lighter-model comparisons use','Reduced-budget comparisons use'),
('Historical permutation uses','Feature-wise permutation uses'),
('New exploratory geometry12 testing uses','Exploratory geometric selection uses'),
('After the geometry12 results were known, an exploratory amendment extended this fixed ordering to every count under the unchanged primary protocol. The count-12 and full-array metrics were reused from the exact matched predictions, and remaining subsets were fitted separately.','The complete geometric count curve evaluates this ordering under the primary protocol. It is a post-hoc analysis motivated by the twelve-electrode comparison.'),
('CPU RF fits overlapped with early folds of this experiment, so these are observed workstation timings rather than an isolated runtime benchmark.','Runtime measurements include concurrent workstation load and are descriptive rather than an isolated benchmark.'),
('differ from the historical method','differ from feature-wise permutation'),
("Primary full16, SHAP12 and geometry12 models were rerun to retain predictions indexed to the same canonical outer-test rows. Full16 and SHAP12 scores must reproduce the original curve within $10^{-6}$.",'Primary full16, SHAP12 and geometry12 predictions are indexed to identical outer-test observations.'),
('uses the pre-existing 200-tree','uses a 200-tree'),
('the original five-fold median/MAD aggregation rule','the five-fold median/MAD aggregation rule'),
('The historical pooled feature thresholds','The pooled feature thresholds'),
('To quantify Monte Carlo decision sensitivity near the boundary, a post-hoc diagnostic repeated the original percentile bootstrap with 200 seeds drawn once from a generator initialized at 20260728, using 10,000 resamples for each seed. Every seed outcome is retained; the diagnostic never replaces the original seed or decision.','A post-hoc Monte Carlo sensitivity analysis repeated the percentile bootstrap under 200 fixed randomizations, with 10,000 resamples per repetition. The distribution of decisions quantifies numerical sensitivity near the boundary; it does not estimate the probability that non-inferiority is true.'),
('in the Supplementary and machine-readable outputs','in the Supplementary'),
])
edit('sections/results.tex',[
('The original percentile decision','The primary percentile decision'),
('The original four penalty curves','The four penalty curves'),
('In the original lighter-model experiment','With the reduced-budget classifier'),
('The subsequently completed fixed geometric curve','The full fixed geometric curve'),
('(A) Historical six-method comparison','(A) Six-method comparison'),
('None of the original','None of the'),
(r'The reverse split met the percentile criterion in \RevFixedSwapSeedHits\ of \RevFixedSwapSeedN\ bootstrap seed reruns (\RevFixedSwapSeedPercent\%); this indicates numerical decision fragility, not a probability that NI is true. The original seed decision is retained.',r'The reverse split met the percentile criterion in \RevFixedSwapSeedHits\ of \RevFixedSwapSeedN\ Monte Carlo repetitions (\RevFixedSwapSeedPercent\%), indicating numerical decision fragility rather than a probability that non-inferiority is true.'),
('the historical percentile criterion','the percentile criterion'),
('the historical Holm rule','the percentile-tail Holm rule'),
])
edit('sections/discussion.tex',[
('under the original margin and decision rule','under the primary margin and decision rule'),
('attribute historical differences solely','attribute differences solely'),
('historical development exposure','development exposure'),
(' Such a protocol is a proposal, not evidence supplied by the present datasets.',''),
])
# Condense supplementary exposition into a scientific supplement.
p=SRC/'supplementary.tex';s=p.read_text(encoding='utf-8')
s=s.replace(r'\newcommand{\rev}[1]{#1}\newcommand{\chg}[1]{#1}','')
s=replace_between(s,'This supplement distinguishes',r'\section{Feature-chain and threshold checks}',r'''This supplement provides detailed methods, exploratory analyses and participant-level results for the electrode-reduction study.

\section{Analysis design and scope}
The primary endpoint is participant Macro-F1, evaluated against a 0.02 engineering tolerance using a participant-bootstrap percentile interval. The analysis design followed pilot work and was not independently preregistered. Model-budget calibration used outer-fold outcomes for participants 1 and 7. Count-feature thresholds were calibrated from pooled recordings before participant partitioning; exclusion of individual participants did not change the rounded thresholds. These development exposures limit prospective interpretation despite participant-disjoint model fitting, scaling and ranking.

Secondary test families and the participant-level aggregation, full geometric count curve, shared-resource comparison, gesture analysis, fixed-layout analyses and Monte Carlo sensitivity are exploratory or post-hoc. The full geometric curve was motivated by the twelve-electrode comparison. Selector activity is a post-hoc descriptive analysis of the penalty results. These analyses are not independent prospective validation. No independently collected cohort with the same GRABMyo montage was available.''')
s=replace_between(s,r'\section{Feature-chain and threshold checks}',r'For one channel,',r'''\section{Signal processing and feature definitions}
The primary active cache contains \GRABMyoActiveWindows\ windows. Participant exclusion reproduced the rounded monopolar threshold in \LOOMonoIdentical\ of \LOOMonoFolds\ folds and the DB5 threshold in \LOODBFiveIdentical\ of \LOODBFiveFolds\ folds. This numerical invariance does not imply fold-specific threshold calibration. Amplitude units and quantized DB5 values are distinct. Rest-inclusive and alternate-window features are extracted from raw recordings without crossing trial boundaries.

For DB5, the filter function limits the upper cutoff to $\min(f_{\rm requested},0.45f_s-1)$, yielding an effective passband of \RevDBFiveBandLow--\RevDBFiveBandHigh\ Hz. The band-pass design argument is four, giving eight poles before forward--backward application. GRABMyo's 450 Hz upper limit is below the clipping cap.''')
s=s.replace('The historical feature-redundancy diagnostic','The feature-redundancy diagnostic')
s=s.replace('The original count decision uses the percentile lower bound. Its original Holm tail is retained explicitly as a historical calculation. The new bootstrap constructs','The primary count decision uses the percentile lower bound. The percentile-tail Holm calculation uses unshifted bootstrap differences and is not a null-generated test. The null-centred studentized sensitivity constructs')
s=s.replace('Historical secondary families contain eight attribution-versus-random tests, twelve original penalty tests and fifteen deletion tests.','Post-hoc secondary families contain eight attribution-versus-random tests, twelve fold-aggregation penalty tests and fifteen deletion tests.')
s=s.replace('the new shared-resource comparison','the shared-resource comparison')
s=s.replace(' No favorable seed is substituted near a boundary.','')
s=s.replace('the historical tail-Holm calculation','the percentile-tail Holm calculation')
s=s.replace('This small-cohort disagreement is reported rather than used to select a favorable test.','This disagreement limits the small-cohort inference.')
s=s.replace("Each revision prediction file stores canonical cache row indices, true labels and model predictions. The full16 and SHAP12 reruns reproduce original participant metrics within $10^{-6}$.",'Full16, SHAP12 and geometry12 predictions use matched outer-test observations and true labels.')
s=s.replace('Gesture numbers follow MotionSequence.txt, whose explicit numeric order is authoritative. In particular, gesture 14 is forearm pronation; visual row order in GestureList.JPG is not used to assign numeric IDs.','Gesture numbers follow the explicit numeric order in MotionSequence.txt; gesture 14 is forearm pronation.')
s=s.replace(r'\section{Participant-level attribution and provenance}',r'\section{Participant-level attribution and selector activity}')
s=replace_between(s,"The old extension's saved hash",r'\section{Resources, sensitivity and fixed-layout validation}',r'''A post-hoc descriptive analysis quantifies whether each fixed penalty changes the unordered physical site set relative to its unpenalized counterpart. It covers every count and participant for both aggregation rules and reports changed-set counts and mean Jaccard similarity. Identical site sets produce identical classifier inputs under the fixed protocol; identical scores in this case are not evidence of equivalence between different layouts.''')
s=s.replace('The historical selection methods','The reduced-budget selection methods').replace('Historical RBF-SVM','RBF-SVM').replace(', with seed 20260728','')
s=s.replace('The new comparison instead shares','The resource-matched comparison shares').replace('the pre-existing RF parameters','these RF parameters')
s=s.replace('the original five-fold median/MAD rule','the five-fold median/MAD rule').replace('Historical pooled feature thresholds','Pooled feature thresholds')
s=s.replace(r'A post-hoc diagnostic reran the percentile bootstrap with \RevFixedSwapSeedN\ fixed seeds; the reverse layout qualified in \RevFixedSwapSeedHits\ reruns. All seed outcomes are retained, and the original seed is unchanged. This diagnoses Monte Carlo sensitivity rather than the probability that the hypothesis is true.',r'A post-hoc Monte Carlo analysis repeated the percentile bootstrap under \RevFixedSwapSeedN\ fixed randomizations, each using 10,000 resamples; the reverse layout qualified in \RevFixedSwapSeedHits\ repetitions. This diagnoses numerical decision sensitivity rather than the probability that the hypothesis is true.')
s=s.replace('Historical full-array classifier context.','Full-array classifier comparison.').replace('unequal budgets and historical calibration','unequal budgets and budget calibration')
s=s.replace('Asterisks, if present, mark','Asterisks mark')
s=s.replace(' The full geometric curve was added after geometry12 had been examined.','')
s=replace_between(s,r'\section{Machine-readable evidence and reproduction}',r'\end{document}',r'''\section{Supplementary data}
Full-precision CSV files provide participant-level scores, statistical contrasts and figure source data. Raw recordings are available from the public dataset repositories identified in the main article.''')
s=s.replace(r'\FloatBarrier'+'\n'+r'\section{Supplementary data}'+'\n'+r'Full-precision CSV files provide participant-level scores, statistical contrasts and figure source data. Raw recordings are available from the public dataset repositories identified in the main article.','')
s=s.replace('This supplement provides detailed methods, exploratory analyses and participant-level results for the electrode-reduction study.','This supplement provides detailed methods, exploratory analyses and participant-level results for the electrode-reduction study. Full-precision CSV files accompany the result tables and figures. Raw recordings are available from the public dataset repositories identified in the main article.')
s=s.replace('Asterisks mark Holm-adjusted signed-rank significance across sixty comparisons.','The inferential family comprises sixty paired signed-rank comparisons with Holm adjustment.')
p.write_text(s,encoding='utf-8')
p=SRC/'main.tex';s=p.read_text(encoding='utf-8').replace(r'\bibliographystyle{plainnat}\bibliography{references}',r'\begingroup\small\setlength{\bibsep}{2pt}\bibliographystyle{plainnat}\bibliography{references}\endgroup');p.write_text(s,encoding='utf-8')
# Polish generated captions without changing numeric payloads.
edit('generated/selection_change_interpretation.tex',[
('The same fixed-protocol cached fits were reused for these identical inputs, giving identical recorded scores; this is input identity rather than an equivalence test of different layouts.','These identical inputs give identical scores under the fixed classifier protocol; this is not an equivalence test of different layouts.'),
])
edit('generated/geometric_curve.tex',[
('Count 12 and full16 reuse the exact matched metrics; remaining subsets were fitted separately. ',' '),
('; geometry12 outcomes were known before this additional curve was planned',''),
])
edit('generated/selection_changes.tex', [(' No new models or equivalence tests were added.',' Identical site sets do not constitute an equivalence test of distinct layouts.')])
edit('generated/participant_extension.tex',[('Fresh isolated participant-level extension minus original fold aggregation','Participant-level minus fold aggregation')])
edit('generated/ni_audit.tex',[
('the historical percentile rule, original percentile-tail Holm calculation','the primary percentile rule, percentile-tail Holm calculation'),
('Historical Holm','Tail Holm'),
])
edit('tables/tab_sparse_ni.tex',[
('Holm: the same decision after Holm correction over the 15 subset sizes.','Holm: the percentile-tail calculation with Holm correction over the 15 subset sizes; this is not a null-generated test.'),
('count-inference audit table','count-inference comparison table'),
])
edit('tables/tab_replication.tex',[
('after Holm correction over 15 subset sizes','under percentile-tail Holm correction over 15 subset sizes'),
('Bootstrap reruns: number of 200 reruns of the bootstrap with different random seeds','Monte Carlo repetitions: number of 200 bootstrap repetitions'),
])
edit('tables/tab_bipolar.tex',[('Bootstrap reruns: as in the DB5 table','Monte Carlo repetitions: as in the DB5 table')])
edit('tables/tab_h2.tex',[('secondary family of 8 tests, Holm-corrected; the detailed test family was specified after the underlying results were available','post-hoc secondary family of 8 tests, Holm-corrected')])
edit('generated/selection_costs.tex',[('Early folds overlapped CPU RF fits, so timings are observational rather than an isolated benchmark.','Measurements include concurrent workstation load and are descriptive rather than an isolated benchmark.')])
# Remove revision wrappers and neutralize technical identifiers in the native reader sources.
def unwrap(s,cmd):
    start='\\'+cmd+'{'
    while start in s:
        i=s.index(start);j=i+len(start);depth=1;k=j
        while depth:
            if s[k]=='{':depth+=1
            elif s[k]=='}':depth-=1
            k+=1
        s=s[:i]+s[j:k-1]+s[k:]
    return s
for p in SRC.rglob('*.tex'):
    s=p.read_text(encoding='utf-8')
    for cmd in ('rev','chg'):s=unwrap(s,cmd)
    s=re.sub(r'(?m)^\s*%[^\n]*\n','',s)
    s=s.replace('revision_macros','analysis_macros').replace('RevFixedSwapSeed','FixedLayoutMonteCarlo').replace('DBFiveSeed','DBFiveMonteCarlo').replace('BipSeed','BipolarMonteCarlo')
    s=s.replace('Historical $p$','Percentile-tail $p$').replace('historical attribution-versus-random','attribution-versus-random')
    s=s.replace('Bootstrap reruns','Monte Carlo repetitions').replace('bootstrap reruns','Monte Carlo repetitions')
    s=s.replace('Non-inf. in Monte Carlo repetitions',r'\makecell{Qualifying\\repetitions}')
    s=s.replace('tab:niaudit','tab:countinference')
    s=s.replace('figure~\\ref','figure~\\ref')
    if p.name in ('main.tex','supplementary.tex'):
        title='Subject-independent forearm sEMG electrode reduction with cross-fitted attribution and non-inferiority testing'
        if p.name=='supplementary.tex':title='Supplementary material: '+title
        s=s.replace(r'\hypersetup{hidelinks}',r'\hypersetup{hidelinks,pdftitle={'+title+r'},pdfauthor={Minh-Tri Ta, Hoang-Khang Phan, Le-Giang Tran}}')
    s=s.replace('This is not a new independent bootstrap or a claim that the penalty is novel.','Their dispersion does not provide independent fitted-model replicates.')
    p.write_text(s,encoding='utf-8')
p=SRC/'generated/revision_macros.tex';p.replace(SRC/'generated/analysis_macros.tex')
p=SRC/'generated/ni_audit.tex';p.replace(SRC/'generated/count_inference.tex')
p=SRC/'supplementary.tex';s=p.read_text(encoding='utf-8').replace('generated/ni_audit','generated/count_inference');p.write_text(s,encoding='utf-8')
# Keep machine-readable results with the article, without internal work reports.
for folder,name in ((OLD/'tables','data/statistical_results'),(OLD/'figures/source_data','data/figure_data')):
    for p in folder.glob('*.csv'):
        clean_name=p.name.replace('completed_ni_audit','count_inference').replace('kstar_audit','minimum_counts').replace('noninferiority_audit','noninferiority_comparisons').replace('selection_change_audit','selector_activity')
        if 'initial_primary_ni_audit' in p.name:continue
        q=OUT/name/clean_name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
(OUT/'README.md').write_text('''# Electrode reduction study

The main article is manuscript/main.pdf and the supplementary article is manuscript/supplementary.pdf. Native LaTeX sources, vector figures and full-precision supplementary data are included.

Compile from manuscript/ using pdfLaTeX, BibTeX for main, and two further pdfLaTeX passes. The supplementary document needs two pdfLaTeX passes.

Public recordings are available from GRABMyo v1.1.0 on PhysioNet and NinaPro DB5. Executable analyses and exact reproducibility settings are retained separately in manuscript_revision/20261014/reproducibility/.
''',encoding='utf-8')
(private/'presentation_changes.md').write_text('''# Final manuscript presentation

The 2026-10-16 reader-facing articles remove work-progress reports, revision chronology, editing labels, verification gates, source-hash discussions, unexecuted work plans and administrative placeholders. Scientific limitations, exploratory/post-hoc status, adverse findings and numerical Monte Carlo sensitivity remain. Exact pseudorandom settings and author declarations are separate from the reader-facing package. No experiment, metric, confidence limit or decision was changed. The complete 2026-10-14 record is preserved.
''',encoding='utf-8')
print('Prepared',OUT)

