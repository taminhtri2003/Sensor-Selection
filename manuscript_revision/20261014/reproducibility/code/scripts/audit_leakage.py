"""Evidence-based leakage audit; tests cannot erase historical design contamination."""
import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.xai.validation import validate_attribution_tables, validate_sparse_subsets


def main():
    a = ROOT / 'artifacts'
    rankings = pd.read_csv(a / 'rankings/cross_fitted_rankings.csv')
    validate_attribution_tables(
        pd.read_csv(a / 'rankings/cross_fitted_importance_long.csv'),
        pd.read_csv(a / 'rankings/per_subject_attribution.csv'),
        pd.read_csv(a / 'rankings/cross_fitted_scores.csv'), rankings, range(1,44))
    validate_sparse_subsets(pd.read_csv(a / 'metrics/sparse_curve_subject_metrics.csv'),
                            rankings, range(1,44))
    thresholds = pd.read_csv(a / 'sensitivity/loo_threshold_check.csv')
    if not thresholds.identical.all():
        raise ValueError('outer-fold threshold equivalence failed')
    report = {
        'artifact_checks': 'PASS',
        'outer_exclusion': 'Every saved inner attribution partition excludes its outer test participant.',
        'subset_provenance': 'Every sparse subset matches its own outer-training ranking.',
        'thresholds': 'Originally pooled. Post-hoc leave-one-out rule yields identical thresholds; this is equivalence evidence, not proof of prospective fold-local estimation.',
        'lambda': 'Four candidates reported. No lambda selection criterion was prespecified or implemented.',
        'historical_calibration': 'Training budgets were calibrated on held-out folds 1 and 7 (Decision 17). Their prior use prevents an unconditional zero-leakage claim about study development.',
        'limits': 'Artifacts cannot prove the full historical model-fitting process. Training/scaling isolation is additionally checked in source and regression tests.',
        'overall_verdict': 'IMPLEMENTED_RANKING_EXCLUSION_VERIFIED_WITH_DISCLOSED_HISTORICAL_LIMITATIONS'
    }
    (ROOT / 'audit/leakage_audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    (ROOT / 'audit/leakage_audit.md').write_text('# Leakage audit\n\n' + '\n\n'.join(
        f'**{key}:** {value}' for key,value in report.items()) + '\n', encoding='utf-8')
    print(report['overall_verdict'])


if __name__ == '__main__':
    main()
