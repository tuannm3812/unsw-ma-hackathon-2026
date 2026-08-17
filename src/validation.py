import pandas as pd


class InsufficientDataError(ValueError):
    """
    Raised when a chronological split cannot be built because the data
    itself is unusable for it - an unparseable/missing date, or an empty
    training or holdout partition. A subclass of `ValueError` (existing
    `pytest.raises(ValueError, ...)` assertions still match), but callers
    that need to distinguish "this sample is too small/unsuitable" from
    other, unrelated `ValueError`s (e.g. a misconfigured predictor
    allowlist) can catch this specifically instead of every `ValueError`.
    """


def chronological_holdout(
    df: pd.DataFrame,
    date_col: str = "fundraisingDate",
    holdout_start: str = "2024-01-01",
) -> "tuple[pd.DataFrame, pd.DataFrame]":
    """
    Split `df` chronologically on `date_col` into a training partition
    (strictly before `holdout_start`) and a holdout partition (on or after
    `holdout_start`).

    This is the primary evaluation design for this project: a random split
    would let the model "see the future" relative to some training rows,
    which is not a fair test of how the model would perform when deployed
    to score newly-posted loans. Splitting on time keeps evaluation honest.

    Dates are parsed with `utc=True` so naive and timezone-aware timestamps
    compare consistently. Rows with a missing/unparseable date are rejected
    outright (rather than silently dropped or routed to an arbitrary side)
    because a missing date makes chronological placement undefined.
    """
    if date_col not in df.columns:
        raise ValueError(f"Missing required column: {date_col}")

    dates = pd.to_datetime(df[date_col], errors="coerce", utc=True)
    if dates.isna().any():
        missing = int(dates.isna().sum())
        raise InsufficientDataError(
            f"{missing} row(s) have a missing or unparseable {date_col}; "
            "chronological_holdout requires a valid date for every row"
        )

    cutoff = pd.Timestamp(holdout_start, tz="UTC")
    train_mask = dates < cutoff
    holdout_mask = ~train_mask

    train = df.loc[train_mask].copy()
    holdout = df.loc[holdout_mask].copy()

    if train.empty or holdout.empty:
        raise InsufficientDataError(
            "chronological_holdout produced an empty training or holdout partition "
            f"for holdout_start={holdout_start!r}; choose a holdout_start with rows "
            "on both sides"
        )

    # Sort each partition chronologically using the parsed dates as the sort
    # key, without mutating the original date column's representation.
    train = train.loc[dates.loc[train_mask].sort_values().index]
    holdout = holdout.loc[dates.loc[holdout_mask].sort_values().index]

    train_max = dates.loc[train_mask].max()
    holdout_min = dates.loc[holdout_mask].min()
    assert train_max < holdout_min, (
        "chronological_holdout invariant violated: latest training date "
        f"({train_max}) is not before earliest holdout date ({holdout_min})"
    )

    return train, holdout
