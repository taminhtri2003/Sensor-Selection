"""Evaluate person-level robust cross-fitted rankings under a fixed post-hoc protocol.

Reuses only exact P3 fits for identical outer participant and channel set. All
new fits use the original P3 function, seed, sample and model configuration.
Results are isolated from the frozen confirmatory artifacts.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.semg_sparse.xai.cross_fitted import CrossFittedAttribution
from src.semg_sparse.xai.validation import validate_attribution_tables, validate_sparse_subsets

OUT = ROOT / "artifacts/participant_attribution"
PLAN = ROOT / "configs/statistics/participant_attribution_extension.json"
LAMBDAS = (0., .25, .5, 1.)


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def prepare():
    folder = ROOT / "artifacts/rankings"
    files = [folder / name for name in ("cross_fitted_importance_long.csv",
             "per_subject_attribution.csv", "cross_fitted_scores.csv", "cross_fitted_rankings.csv")]
    long, people, scores, ranks = [pd.read_csv(p) for p in files]
    validate_attribution_tables(long, people, scores, ranks, range(1, 44))
    rows, score_rows = [], []
    for pid in range(1, 44):
        mat = people[people.outer_participant == pid].pivot(
            index="attributed_subject", columns="channel", values="importance_norm")
        folds = long[long.outer_participant == pid]
        norm = folds.pivot(index="inner_fold", columns="channel", values="importance_norm").to_numpy()
        held = [[int(s) for s in g.inner_held_subjects.iloc[0].split(";")]
                for _, g in folds.groupby("inner_fold")]
        att = CrossFittedAttribution(norm, norm, held, [],
              per_subject_norm={s: row.to_numpy() for s, row in mat.iterrows()})
        central, mad = att.central("subject"), att.instability("subject")
        for c in range(16):
            score_rows.append({"outer_participant": pid, "channel": c+1,
                               "A_central": central[c], "U_instability": mad[c]})
        for lam in LAMBDAS:
            ranking = [c+1 for c in att.ranking(lam, unit="subject")]
            rows.append({"outer_participant": pid, "lambda": lam,
                         "ranking": ";".join(map(str, ranking))})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "rankings.csv", index=False)
    pd.DataFrame(score_rows).to_csv(OUT / "scores.csv", index=False)
    inputs = files + [PLAN, ROOT / "scripts/26_sparse_sensor_curve.py",
        ROOT / "src/semg_sparse/xai/cross_fitted.py",
        ROOT / "artifacts/metrics/sparse_curve_subject_metrics.csv"]
    inputs += [ROOT / "data/cache" / n for n in ("loso_X.npy", "loso_y.npy", "loso_subj.npy")]
    fingerprints = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    stamp = sha(PLAN)
    return pd.DataFrame(rows), fingerprints, stamp


def fit_missing(job):
    pid, lam, ranking, ks, device = job
    p3 = module("p3", "26_sparse_sensor_curve.py")
    paths = tuple(str(ROOT / "data/cache" / n) for n in ("loso_X.npy", "loso_y.npy", "loso_subj.npy"))
    return p3.run_group((pid, [(lam, ranking)], ks, paths, "XGB", device, 200000, 2, 4))


def analyse(curve):
    stats = module("secondary", "37_secondary_statistics.py")
    original = pd.read_csv(ROOT / "artifacts/metrics/sparse_curve_subject_metrics.csv")
    comparisons, ni = [], []
    for lam in LAMBDAS:
        for k in range(1, 16):
            comparisons.append(stats.paired(
                stats.series(curve, **{"lambda": lam}, channels_k=k),
                stats.series(original, **{"lambda": lam}, channels_k=k),
                **{"lambda": lam}, k=k, comparison="subject minus fold aggregation"))
        ni.append(stats.holm_ni(curve, 16, "participant_attribution_posthoc", lam=lam))
    stats.finish(comparisons, "participant_vs_fold_posthoc", True).to_csv(
        OUT / "paired_comparisons.csv", index=False)
    pd.concat(ni).to_csv(OUT / "non_inferiority.csv", index=False)
    curve.groupby(["lambda", "channels_k"]).agg(
        n_participants=("participant_id", "nunique"), mean_macro_f1=("macro_f1", "mean")
    ).reset_index().to_csv(OUT / "summary.csv", index=False)


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare-only", action="store_true")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-dir", type=Path, default=OUT, help="isolated output for provenance-compatible refits")
    args = ap.parse_args()
    OUT = args.out_dir.resolve()
    ranks, fingerprints, stamp = prepare()
    manifest = OUT / "input_hashes.json"
    if (manifest.exists() and json.loads(manifest.read_text()) != fingerprints
            and (OUT / "sparse_curve.csv").exists()):
        raise ValueError("inputs changed: archive prior extension output before rerunning")
    manifest.write_text(json.dumps(fingerprints, indent=2), encoding="utf-8")
    if args.prepare_only:
        print("Prepared complete participant-balanced rankings; no performance outcomes selected.")
        return
    original = pd.read_csv(ROOT / "artifacts/metrics/sparse_curve_subject_metrics.csv")
    validate_sparse_subsets(original, pd.read_csv(ROOT / "artifacts/rankings/cross_fitted_rankings.csv"), range(1,44))
    if set(original.n_train_windows) != {200000} or original.model.nunique() != 1:
        raise ValueError("original curve is not the expected P3 protocol")
    result_path = OUT / "sparse_curve.csv"
    existing = pd.read_csv(result_path).to_dict("records") if result_path.exists() else []
    done = {(int(r['participant_id']), float(r['lambda']), int(r['channels_k'])): r for r in existing}
    cache = {}
    for index, r in original.iterrows():
        key = (int(r.participant_id), tuple(sorted(int(c) for c in str(r.channels).split(';'))))
        if key in cache and not np.isclose(cache[key]['macro_f1'], r.macro_f1, atol=1e-6):
            raise ValueError("duplicate original channel sets have inconsistent metrics")
        cache[key] = {**r.to_dict(), "evaluation_source": "original_p3", "source_row": int(index)}
    for r in existing:
        key = (int(r['participant_id']), tuple(sorted(int(c) for c in str(r['channels']).split(';'))))
        cache[key] = r
    for pid in range(1,44):
        new_fits = 0
        for _, rr in ranks[ranks.outer_participant == pid].iterrows():
            lam = float(rr['lambda'])
            ranking = [int(c) for c in rr.ranking.split(';')]
            pending = []
            for k in range(1,17):
                if (pid, lam, k) in done:
                    continue
                key = (pid, tuple(sorted(ranking[:k])))
                if key not in cache:
                    pending.append(k)
            if pending:
                with ProcessPoolExecutor(max_workers=1) as ex:
                    fitted = ex.submit(fit_missing, (pid, lam, ranking, pending, args.device)).result()
                for r in fitted:
                    key = (pid, tuple(sorted(int(c) for c in r['channels'].split(';'))))
                    cache[key] = {**r, "evaluation_source": "new_p3_protocol_fit", "source_row": -1}
                new_fits += len(fitted)
            for k in range(1,17):
                key = (pid, tuple(sorted(ranking[:k])))
                r = cache[key]
                done[pid, lam, k] = {**r, "participant_id": pid, "lambda": lam,
                    "channels_k": k, "channels": ';'.join(map(str, ranking[:k])), "plan_sha256": stamp}
            result = pd.DataFrame(done.values()).sort_values(['participant_id', 'lambda', 'channels_k'])
            temp = result_path.with_suffix('.tmp')
            result.to_csv(temp, index=False)
            temp.replace(result_path)
        print(f"Participant {pid}/43 complete; {new_fits} new fits", flush=True)
    curve = pd.read_csv(result_path)
    validate_sparse_subsets(curve, ranks, range(1,44))
    analyse(curve)
    print("PASS: participant-level attribution extension complete", flush=True)


if __name__ == '__main__':
    main()
