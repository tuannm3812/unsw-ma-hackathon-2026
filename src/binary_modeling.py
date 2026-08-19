"""
Leakage-safe chronological classification of the 24-hour funding outcome.

The design spec's Validation section commits to a specific predictive
evaluation for the binary target: "The 24-hour classifier will report ROC
AUC, PR AUC, and calibration or Brier score when both classes are present."
Before this module, that promise was unfulfilled - the only 24-hour model
in the codebase was `src/statistical_analysis.py`'s *explanatory* binomial
GLM, which answers "how is each predictor associated with 24-hour
funding," not "how well can 24-hour funding be predicted out-of-sample."
On the ~100-row development sample that GLM also fails via quasi-complete
separation, so there was no working binary evaluation of any kind.

This module fits exactly one classifier, `HistGradientBoostingClassifier`
- the same scikit-learn-native, no-extra-dependency choice
`src/advanced_modeling.py` already uses for the continuous nonlinear
benchmark, for the same reason (avoids adding `xgboost`/`lightgbm` for a
single reference point). It reuses `prepare_chronological_matrices`
(`src/modeling.py`) for the exact same leakage-safe chronological
train/holdout split and preprocessing the continuous benchmarks use - not
a re-derived split - so `X_train`/`X_holdout` are identical across every
predictive model in this project; only the target and estimator differ
here.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

try:
    from src.modeling import prepare_chronological_matrices
    from src.validation import InsufficientDataError
except ModuleNotFoundError:
    from modeling import prepare_chronological_matrices
    from validation import InsufficientDataError


def evaluate_chronological_binary_classifier(
    df: pd.DataFrame,
    holdout_start: str = "2024-01-01",
    n_topics: int = 5,
    random_state: int = 42,
) -> dict:
    """
    Fit a leakage-safe chronological classifier for `funded_within_24h` and
    report ROC AUC, PR AUC, and Brier score on the untouched holdout split,
    per the design spec's Validation section.

    A chronological split (unlike a random one) is not guaranteed to leave
    both classes in the holdout partition - e.g. every loan posted after
    `holdout_start` could happen to fund within 24h, or none could. ROC
    AUC/PR AUC are mathematically undefined with only one class present in
    `y_true`, so this is checked explicitly and reported as a labeled
    diagnostic (`roc_auc`/`pr_auc` set to `None`, `single_class_holdout`
    set to `True`) rather than letting scikit-learn raise an opaque
    `ValueError` or silently returning a meaningless number. Brier score
    and holdout accuracy remain well-defined regardless of class balance,
    so they are always reported. The training partition having only one
    class is a harder failure (a classifier cannot be fit on it at all)
    and raises `InsufficientDataError`, mirroring how
    `prepare_chronological_matrices` itself raises when a split is too
    small to support any model.

    Returns a dict with row counts, feature names, a `"metrics"` dict
    (`roc_auc`, `pr_auc`, `brier_score`, `holdout_accuracy`,
    `single_class_holdout`, `holdout_class_balance`), and a private
    `_artifacts` key holding the fitted classifier and the matrices from
    `prepare_chronological_matrices` - callers that serialize this dict to
    a report should drop `_artifacts` first.
    """
    matrices = prepare_chronological_matrices(df, holdout_start=holdout_start, n_topics=n_topics)
    artifacts = matrices["_artifacts"]

    X_train, X_holdout = artifacts["X_train"], artifacts["X_holdout"]
    y_train, y_holdout = artifacts["y_train_binary"], artifacts["y_holdout_binary"]

    if len(np.unique(y_train)) < 2:
        raise InsufficientDataError(
            "evaluate_chronological_binary_classifier requires both "
            "funded_within_24h classes (0 and 1) in the training partition "
            f"to fit a classifier at all; got only class {int(y_train[0])} "
            f"across {len(y_train)} training rows for holdout_start="
            f"{holdout_start!r}. Choose a different holdout_start or "
            "provide more rows."
        )

    classifier = HistGradientBoostingClassifier(random_state=random_state)
    classifier.fit(X_train, y_train)

    holdout_pred_proba = classifier.predict_proba(X_holdout)[:, 1]
    holdout_pred_label = (holdout_pred_proba >= 0.5).astype(int)

    single_class_holdout = len(np.unique(y_holdout)) < 2
    metrics = {
        "roc_auc": None if single_class_holdout else float(roc_auc_score(y_holdout, holdout_pred_proba)),
        "pr_auc": None if single_class_holdout else float(average_precision_score(y_holdout, holdout_pred_proba)),
        "brier_score": float(brier_score_loss(y_holdout, holdout_pred_proba)),
        "holdout_accuracy": float((holdout_pred_label == y_holdout).mean()),
        "single_class_holdout": bool(single_class_holdout),
        "holdout_class_balance": {
            "funded_within_24h": int(y_holdout.sum()),
            "not_within_24h": int(len(y_holdout) - y_holdout.sum()),
        },
    }

    artifacts["binary_classifier"] = classifier

    return {
        "holdout_start": matrices["holdout_start"],
        "train_rows": matrices["train_rows"],
        "holdout_rows": matrices["holdout_rows"],
        "feature_names": matrices["feature_names"],
        "metrics": metrics,
        "_artifacts": artifacts,
    }
