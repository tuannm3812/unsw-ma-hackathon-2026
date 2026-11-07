"""Data contract for the separate, retrospective matched-text benchmark."""
from __future__ import annotations

import hashlib
import re

import numpy as np
import pandas as pd

from src.data_loader import prepare_analysis_data
from src.features import FRAMING_PATTERNS, clean_html, extract_deterministic_features
from src.validation import InsufficientDataError

S_NUMERIC = [
    'borrowerCount', 'is_group_loan', 'log_loan_amount',
    'lenderRepaymentTerm', 'fundraising_year', 'fundraising_month',
]
S_CATEGORICAL = [
    'gender_classification', 'loan_size_band', 'repaymentInterval',
    'country_iso', 'region', 'sector', 'activity',
]
METADATA = [
    'description_missing', 'desc_word_count', 'desc_char_count',
    'desc_sentence_count', 'desc_avg_word_length', 'desc_avg_sentence_length',
]
LEXICAL = [f'{name}_mentions_per_100_words' for name in FRAMING_PATTERNS] + [
    'number_token_count', 'age_pattern_count', 'years_in_business_count',
    'desc_sentiment_compound', 'desc_sentiment_pos', 'desc_sentiment_neg',
    'desc_sentiment_neu', 'sentiment_available',
]


def feature_registry() -> dict[str, list[str]]:
    """Return the disjoint posting-field blocks; P remains an unvalidated proxy."""
    return {'S_numeric': list(S_NUMERIC), 'S_categorical': list(S_CATEGORICAL),
            'M': list(METADATA), 'L': list(LEXICAL),
            'R': ['description_clean'], 'P': ['programme_proxy']}


def calendar_split(prepared: pd.DataFrame, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return integer row positions, requiring completed membership before cutoff.

    Evaluation includes eventual completions in a posting-year window. It does
    not reconstruct all listings, and current snapshot fields are not verified
    historical versions of those fields.
    """
    if not prepared.index.is_unique:
        raise ValueError('calendar_split requires a unique input index')
    cutoff = pd.Timestamp(f'{year}-01-01', tz='UTC')
    end = pd.Timestamp(f'{year + 1}-01-01', tz='UTC')
    posted = pd.to_datetime(prepared['fundraisingDate'], errors='coerce', utc=True)
    completed = pd.to_datetime(prepared['raisedDate'], errors='coerce', utc=True)
    valid = prepared['valid_completed_outcome'].fillna(False).astype(bool)
    train = np.flatnonzero((valid & posted.lt(cutoff) & completed.lt(cutoff)).to_numpy())
    test = np.flatnonzero((valid & posted.ge(cutoff) & posted.lt(end)).to_numpy())
    if not len(train) or not len(test):
        raise InsufficientDataError(f'empty as-of train or evaluation window for {year}')
    return train, test


def text_signature(text: object, *, template: bool = False) -> str:
    """Hash normalised text; digit normalisation is only a template proxy."""
    value = clean_html(text).lower()
    if not value:
        return ''
    if template:
        value = re.sub(r'\b\d+(?:[.,]\d+)*\b', '#', value)
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _counts(values: pd.Series) -> dict[str, int]:
    return {str(k): int(v) for k, v in values.value_counts(dropna=False).items()}


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    # Pandas otherwise infers one string format from the first row; mixed
    # date-only/ISO timestamps would silently become missing outcomes.
    parsed = df.copy()
    for column in ['fundraisingDate', 'raisedDate', 'disbursalDate']:
        if column in parsed:
            parsed[column] = pd.to_datetime(parsed[column], format='mixed', errors='coerce', utc=True)
    return prepare_analysis_data(parsed)


def audit_availability(df: pd.DataFrame, years: list[int]) -> dict:
    """Return aggregate eligibility, maturity and duplication evidence only."""
    prepared = _prepare(df.reset_index(drop=True))
    valid = prepared.loc[prepared['valid_completed_outcome']]
    signatures = valid['description'].map(text_signature)
    observed = signatures.ne('')
    identifiers = df['id'] if 'id' in df else pd.Series(dtype='object')
    rows = []
    for year in years:
        cutoff = pd.Timestamp(f'{year}-01-01', tz='UTC')
        end = pd.Timestamp(f'{year + 1}-01-01', tz='UTC')
        before = valid['fundraisingDate'].lt(cutoff)
        unavailable = before & valid['raisedDate'].ge(cutoff)
        evaluation = valid['fundraisingDate'].ge(cutoff) & valid['fundraisingDate'].lt(end)
        crossing = valid.loc[unavailable]
        rows.append({
            'year': int(year), 'cutoff': cutoff.isoformat(),
            'posting_only_train_rows': int(before.sum()),
            'asof_train_rows': int((before & ~unavailable).sum()),
            'unavailable_completed_membership_rows': int(unavailable.sum()),
            'crossing_duration_quantiles_days': {
                str(q): float(v) for q, v in
                crossing['funding_speed_days'].quantile([.5, .9, .99]).dropna().items()},
            'crossing_rows_by_country': _counts(crossing['country_iso']),
            'evaluation_rows': int(evaluation.sum()),
            'evaluation_status_counts': _counts(valid.loc[evaluation, 'status']),
            'evaluation_posting_min': (valid.loc[evaluation, 'fundraisingDate'].min().isoformat()
                                       if evaluation.any() else None),
            'evaluation_posting_max': (valid.loc[evaluation, 'fundraisingDate'].max().isoformat()
                                       if evaluation.any() else None),
        })
    return {
        'input_rows': len(df), 'eligible_rows': len(valid),
        'excluded_rows': len(df) - len(valid),
        'exclusions': _counts(prepared.loc[~prepared['valid_completed_outcome'], 'outcome_issue']),
        'status_counts': _counts(valid['status']),
        'duplicate_id_rows': int(identifiers.dropna().duplicated(keep=False).sum()),
        'missing_id_rows': int(identifiers.isna().sum()),
        'duplicate_description_rows': int(signatures[observed].duplicated(keep=False).sum()),
        'missing_description_rows': int((~observed).sum()), 'windows': rows,
        'boundary': 'Completed-only snapshot; field histories and extract timestamp unverified. '
                    'As-of membership is enforced for training, but evaluation remains selected '
                    'on eventual completion. Snapshot text may have been edited after posting.',
    }


def build_benchmark_frame(df: pd.DataFrame, chunk_size: int = 25000) -> pd.DataFrame:
    """Compute source-defined deterministic features in bounded chunks.

    Original input positions provide private identity; IDs and raw name fields
    are discarded. No estimated transform is fitted here. Frequency-dependent
    region/sector groupings from the source extractor are deliberately unused.
    """
    if chunk_size < 1 or df.empty:
        raise ValueError('positive chunk_size and nonempty data are required')
    registry = feature_registry()
    columns = S_NUMERIC + S_CATEGORICAL + METADATA + LEXICAL
    outcomes = ['fundraisingDate', 'raisedDate', 'funding_speed_days',
                'log_funding_speed', 'funded_within_24h', 'valid_completed_outcome', 'status']
    pieces = []
    for start in range(0, len(df), chunk_size):
        raw = df.iloc[start:start + chunk_size].copy().reset_index(drop=True)
        raw.index = np.arange(start, start + len(raw))
        prepared = _prepare(raw)
        features = extract_deterministic_features(prepared)
        piece = features[columns + outcomes].copy()
        piece['description_clean'] = features['clean_description']
        piece['programme_proxy'] = raw['whySpecial'].astype('string').str.strip().fillna('')
        piece['description_signature'] = raw['description'].map(text_signature)
        piece['template_signature'] = raw['description'].map(lambda x: text_signature(x, template=True))
        for column in registry['S_numeric'] + METADATA + LEXICAL:
            piece[column] = pd.to_numeric(piece[column], errors='coerce').astype('float32')
        for column in S_CATEGORICAL:
            piece[column] = piece[column].astype('string').fillna('__MISSING__').astype(object)
        pieces.append(piece)
        print(f'Deterministic features: {start + len(raw):,}/{len(df):,}', flush=True)
    return pd.concat(pieces)
