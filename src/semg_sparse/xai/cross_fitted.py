"""Cross-fitted attribution with per-fold retention, for stability-regularised sensor ranking.

Why this exists alongside shap_attributions.py: the original module averages out-of-fold SHAP
over every inner fold and returns a single importance vector. That discards fold identity, so
attribution *stability* — the quantity the study is about — cannot be computed from its output
at all. This module returns the full (n_inner_folds x n_channels) matrix instead.

Attribution is computed with XGBoost's native `pred_contribs=True`, which is exact TreeSHAP and
runs on the GPU (~5 s for 20k samples x 16 classes, versus minutes for shap.TreeExplainer).

Leakage contract: every function here is given outer-training data only. The held-out outer
participant is never passed in, so it can influence neither the model, the scaler, nor the
resulting channel ranking.
"""

from dataclasses import dataclass, field

import numpy as np
import xgboost as xgb
from sklearn.model_selection import GroupKFold


@dataclass
class CrossFittedAttribution:
    """Per-inner-fold channel attribution and the rankings derived from it."""
    importance_raw: np.ndarray        # (n_folds, n_channels) mean |phi| per channel
    importance_norm: np.ndarray       # (n_folds, n_channels) rows sum to 1
    fold_subjects: list               # subjects held out in each inner fold
    n_attrib_samples: list            # samples attributed per fold
    # Per-individual attribution: subject id -> (n_channels,) normalised importance.
    # Fold-level importance averages over a whole group of held-out subjects, which smooths away
    # individual variation; agreement between groups is a weaker claim than agreement between
    # people. This keeps the per-person vectors so the stronger claim can actually be tested.
    per_subject_norm: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    def aggregation_matrix(self, unit="fold"):
        """Return independent attribution units, without pooling people into folds.

        ``subject`` is a post-hoc alternative to the original fold estimand. Every
        inner-held-out person must be represented exactly once; missing people
        must never silently change the population being ranked.
        """
        if unit == "fold":
            values = np.asarray(self.importance_norm, dtype=float)
        elif unit == "subject":
            subjects = [s for fold in self.fold_subjects for s in fold]
            if len(subjects) != len(set(subjects)):
                raise ValueError("attributed subjects occur in multiple inner folds")
            if set(subjects) != set(self.per_subject_norm):
                raise ValueError("subject aggregation requires every inner-held-out subject")
            values = np.asarray([self.per_subject_norm[s] for s in sorted(subjects)])
        else:
            raise ValueError("aggregation unit must be 'fold' or 'subject'")
        if (values.ndim != 2 or not len(values) or not np.isfinite(values).all()
                or (values < 0).any() or not np.allclose(values.sum(axis=1), 1.0)):
            raise ValueError("attributions must be finite nonnegative normalised vectors")
        return values

    def central(self, unit="fold"):
        """A_c — central attribution magnitude across inner folds (median: robust to one odd fold)."""
        return np.median(self.aggregation_matrix(unit), axis=0)

    def instability(self, unit="fold"):
        """U_c — median absolute deviation of each channel's attribution across inner folds."""
        values = self.aggregation_matrix(unit)
        med = np.median(values, axis=0, keepdims=True)
        return np.median(np.abs(values - med), axis=0)

    def score(self, lam=0.0, unit="fold"):
        """Q_c(lambda) = A_c - lambda * U_c. lambda=0 recovers plain magnitude ranking."""
        if not np.isfinite(lam) or lam < 0:
            raise ValueError("lambda must be finite and nonnegative")
        return self.central(unit) - lam * self.instability(unit)

    def ranking(self, lam=0.0, unit="fold"):
        """Channel ids (0-indexed) ordered most to least important under Q_c(lambda)."""
        q = self.score(lam, unit)
        # Deterministic tie-break by channel id so runs are reproducible.
        return list(np.lexsort((np.arange(len(q)), -q)))


def assert_channel_major(feature_names, n_channels, n_features_per_channel):
    """Verify columns are grouped channel-major before any reshape relies on it.

    The channel attribution step reshapes the flat feature axis to (n_channels,
    n_features_per_channel). That is only valid if all of channel 1's features come first, then
    channel 2's, and so on. Silently violating this would mix channels together and produce a
    plausible-looking but meaningless ranking, so it is checked rather than assumed.
    """
    expected = n_channels * n_features_per_channel
    if len(feature_names) != expected:
        raise ValueError(f"expected {expected} features, got {len(feature_names)}")
    for c in range(n_channels):
        block = feature_names[c * n_features_per_channel:(c + 1) * n_features_per_channel]
        prefix = f"ch{c + 1}_"
        bad = [n for n in block if not n.startswith(prefix)]
        if bad:
            raise ValueError(
                f"feature columns are not channel-major: block {c} should all start with "
                f"'{prefix}' but contains {bad[:3]}"
            )


def channel_importance_from_contribs(contribs, n_channels, n_features_per_channel):
    """Reduce SHAP contributions to one importance value per channel.

    contribs: (n_samples, n_classes, n_features + 1) or (n_samples, n_features + 1).
    The trailing column is the bias term and is dropped. Returns (n_channels,).
    """
    a = np.asarray(contribs)
    if (a.ndim not in (2, 3) or a.shape[-1] != n_channels * n_features_per_channel + 1
            or a.shape[0] == 0 or not np.isfinite(a).all()):
        raise ValueError("invalid SHAP contribution shape or nonfinite/empty contributions")
    if a.ndim == 3:
        a = a[:, :, :-1]                       # drop bias
        a = np.abs(a).mean(axis=1)             # mean |phi| over classes -> (n, n_features)
    else:
        a = np.abs(a[:, :-1])
    n = a.shape[0]
    a = a.reshape(n, n_channels, n_features_per_channel)
    return a.mean(axis=(0, 2))                 # over samples and within-channel features


def compute_cross_fitted_attribution(
    X_train,
    y_train,
    subjects_train,
    feature_names,
    n_channels=16,
    n_features_per_channel=10,
    n_inner_folds=5,
    xgb_params=None,
    device="cuda",
    max_attrib_samples=20000,
    max_train_samples=None,
    min_subject_samples=200,
    seed=20260728,
    excluded_subjects=(),
):
    """Fit inner-fold models on outer-training data and attribute on held-out inner subjects.

    For each inner fold j: train on inner-train subjects, compute SHAP on the inner-validation
    subjects only (out-of-fold), and reduce to per-channel importance I[j, c]. Attribution is
    therefore always measured on subjects the attributing model has not seen.

    max_attrib_samples caps how many validation windows are attributed per fold (uniform random,
    fixed seed). This is a compute bound, not a statistical one — importance is an average over
    windows and is stable well below the cap.
    """
    assert_channel_major(feature_names, n_channels, n_features_per_channel)

    X_train = np.asarray(X_train, dtype=np.float32)
    y_train = np.asarray(y_train)
    subjects_train = np.asarray(subjects_train)
    if (X_train.ndim != 2 or y_train.ndim != 1 or subjects_train.ndim != 1
            or len(X_train) != len(y_train) or len(y_train) != len(subjects_train)
            or X_train.shape[1] != len(feature_names)):
        raise ValueError("features, labels and subjects have incompatible shapes")
    if set(excluded_subjects) & set(subjects_train.tolist()):
        raise ValueError("outer held-out participant present in attribution input")
    if not np.isfinite(X_train).all():
        raise ValueError("attribution features must be finite")

    params = dict(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                  colsample_bytree=0.8, tree_method="hist", random_state=seed, verbosity=0)
    if xgb_params:
        params.update(xgb_params)

    uniq = np.unique(subjects_train)
    n_splits = int(min(n_inner_folds, len(uniq)))
    if n_splits < 2:
        raise ValueError(f"need >=2 training subjects for inner folds, got {len(uniq)}")

    gkf = GroupKFold(n_splits=n_splits)
    rng = np.random.default_rng(seed)

    imp = np.zeros((n_splits, n_channels), dtype=np.float64)
    fold_subjects, n_used = [], []
    per_subject = {}

    for j, (tr, va) in enumerate(gkf.split(X_train, y_train, groups=subjects_train)):
        held = sorted(np.unique(subjects_train[va]).tolist())
        # Inner leakage guard: attribution subjects must be absent from the fitting set.
        if set(held) & set(np.unique(subjects_train[tr]).tolist()):
            raise AssertionError(f"inner fold {j} leaks subjects {set(held) & set(subjects_train[tr])}")

        # Scale within the inner fold: statistics come from inner-train only.
        mu = X_train[tr].mean(axis=0)
        sd = X_train[tr].std(axis=0) + 1e-8

        # Optional training-window cap. XGBoost saturates by ~100-200k windows on this data
        # (decision log 8), so this cuts cost without changing the fitted model materially.
        # Applied after the split, so it can never pull in inner-validation samples.
        fit_idx = tr
        if max_train_samples and len(tr) > max_train_samples:
            fit_idx = rng.choice(tr, size=max_train_samples, replace=False)

        model = xgb.XGBClassifier(device=device, **params)
        model.fit((X_train[fit_idx] - mu) / sd, y_train[fit_idx])

        idx = va
        if max_attrib_samples and len(idx) > max_attrib_samples:
            idx = rng.choice(idx, size=max_attrib_samples, replace=False)

        booster = model.get_booster()
        booster.set_param({"device": device})
        contribs = booster.predict(xgb.DMatrix((X_train[idx] - mu) / sd), pred_contribs=True)

        imp[j] = channel_importance_from_contribs(contribs, n_channels, n_features_per_channel)
        fold_subjects.append(held)
        n_used.append(int(len(idx)))

        # Per-individual aggregation of the SAME contributions — no extra SHAP cost. Each subject
        # here was held out of this inner fold's model, so their attribution is out-of-fold.
        subj_of_sample = subjects_train[idx]
        for s in np.unique(subj_of_sample):
            m = subj_of_sample == s
            if m.sum() < min_subject_samples:
                continue
            v = channel_importance_from_contribs(
                np.asarray(contribs)[m], n_channels, n_features_per_channel)
            total = v.sum()
            per_subject[int(s)] = v / total if total > 0 else v

    row_sums = imp.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return CrossFittedAttribution(
        importance_raw=imp,
        importance_norm=imp / row_sums,
        fold_subjects=fold_subjects,
        n_attrib_samples=n_used,
        per_subject_norm=per_subject,
        meta={"n_inner_folds": n_splits, "xgb_params": params, "seed": seed,
              "max_attrib_samples": max_attrib_samples,
              "max_train_samples": max_train_samples,
              "min_subject_samples": min_subject_samples},
    )
