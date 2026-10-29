"""Fail-closed checks for saved cross-fitted attribution and electrode selections."""
import numpy as np
import pandas as pd


def require_grid(frame, columns, levels, label):
    if frame.duplicated(columns).any():
        raise ValueError(f"{label}: duplicate keys {columns}")
    expected = pd.MultiIndex.from_product(levels, names=columns)
    actual = pd.MultiIndex.from_frame(frame[columns])
    if len(expected.difference(actual)) or len(actual.difference(expected)):
        raise ValueError(f"{label}: incomplete or unexpected grid")


def finite_values(frame, columns, label, bounded=False):
    a = frame[columns].to_numpy(dtype=float)
    if not np.isfinite(a).all() or (bounded and ((a < 0) | (a > 1)).any()):
        raise ValueError(f"{label}: nonfinite or out-of-range values")


def validate_attribution_tables(long, per_subject, scores, ranks, participants,
                                n_channels=16, n_folds=5, lambdas=(0., .25, .5, 1.)):
    """Reconstruct every score/ranking and prove outer/inner subject disjointness."""
    participants = set(participants)
    channels = list(range(1, n_channels + 1))
    require_grid(long, ["outer_participant", "inner_fold", "channel"],
                 [sorted(participants), range(n_folds), channels], "fold attribution")
    require_grid(scores, ["outer_participant", "channel"],
                 [sorted(participants), channels], "scores")
    require_grid(ranks, ["outer_participant", "lambda"],
                 [sorted(participants), lambdas], "rankings")
    if set(per_subject.outer_participant) != participants:
        raise ValueError("per-subject attribution: outer cohort mismatch")
    finite_values(long, ["importance_raw", "importance_norm"], "fold attribution")
    finite_values(per_subject, ["importance_norm"], "person attribution", bounded=True)
    for pid in sorted(participants):
        g = long[long.outer_participant == pid]
        held = []
        for _, f in g.groupby("inner_fold"):
            if f.inner_held_subjects.nunique() != 1:
                raise ValueError("inconsistent inner-fold subject metadata")
            ids = [int(x) for x in str(f.inner_held_subjects.iloc[0]).split(";")]
            held.extend(ids)
            f = f.sort_values("channel")
            raw = f.importance_raw.to_numpy()
            if (raw < 0).any() or raw.sum() <= 0:
                raise ValueError("empty or negative fold attribution")
            if not np.allclose(raw / raw.sum(), f.importance_norm, atol=1e-8):
                raise ValueError("fold attribution normalisation mismatch")
        if len(held) != len(set(held)) or set(held) != participants - {pid}:
            raise ValueError(f"outer fold {pid}: inner held subjects leak, repeat or are missing")
        p = per_subject[per_subject.outer_participant == pid]
        require_grid(p, ["attributed_subject", "channel"],
                     [sorted(participants - {pid}), channels], "person attribution")
        if not np.allclose(p.groupby("attributed_subject").importance_norm.sum(), 1):
            raise ValueError("person attribution not normalised")
        mat = g.pivot(index="inner_fold", columns="channel", values="importance_norm").to_numpy()
        central = np.median(mat, axis=0)
        instability = np.median(abs(mat - central), axis=0)
        s = scores[scores.outer_participant == pid].sort_values("channel")
        if not (np.allclose(s.A_central, central) and np.allclose(s.U_instability, instability)):
            raise ValueError("saved attribution scores differ from fold attributions")
        for lam in lambdas:
            q = central - lam * instability
            if not np.allclose(s[f"Q_lam{lam}"], q):
                raise ValueError("saved Q differs from central minus lambda times instability")
            expected = (np.lexsort((np.arange(n_channels), -q)) + 1).tolist()
            row = ranks[(ranks.outer_participant == pid) & (ranks['lambda'] == lam)].iloc[0]
            actual = [int(x) for x in str(row.ranking).split(";")]
            if expected != actual:
                raise ValueError("saved ranking differs from attribution scores")


def validate_sparse_subsets(curve, ranks, participants, n_channels=16,
                            lambdas=(0., .25, .5, 1.)):
    require_grid(curve, ["participant_id", "lambda", "channels_k"],
                 [sorted(participants), lambdas, range(1, n_channels + 1)], "sparse curve")
    finite_values(curve, ["macro_f1", "accuracy", "balanced_accuracy", "weighted_f1"],
                  "sparse curve metrics", bounded=True)
    lookup = {(int(r.outer_participant), float(r['lambda'])):
              [int(x) for x in str(r.ranking).split(";")] for _, r in ranks.iterrows()}
    for _, row in curve.iterrows():
        actual = [int(x) for x in str(row.channels).split(";")]
        expected = lookup[int(row.participant_id), float(row['lambda'])][:int(row.channels_k)]
        if actual != expected:
            raise ValueError("evaluated subset does not match its outer-training ranking")
