import random

import pandas as pd
import pytest


@pytest.fixture
def synthetic_kiva_df():
    rows = []
    years = [2018, 2020, 2021, 2023, 2024, 2024, 2025, 2025]
    for idx, year in enumerate(years):
        posted = pd.Timestamp(year=year, month=1 + idx % 6, day=10, tz="UTC")
        rows.append({
            "id": idx + 1,
            "status": "funded",
            "borrowerCount": 2 if idx == 2 else 1,
            "name": f"Borrower {idx}",
            "gender": ["female", "male", "female, male", None][idx % 4],
            "loanAmount": 100.0 + 50 * idx,
            "lenderRepaymentTerm": 6 + idx,
            "repaymentInterval": ["monthly", "irregularly", "at_end"][idx % 3],
            "sector": ["Agriculture", "Retail"][idx % 2],
            "activity": "Farming",
            "use": "to buy seeds and tools",
            "city": "Test City",
            "latitude": 0.0,
            "longitude": 0.0,
            "country_iso": ["KE", "PH"][idx % 2],
            "country_name": ["Kenya", "Philippines"][idx % 2],
            "region": ["Africa", "Asia"][idx % 2],
            "country_ppp": 2000.0 + idx,
            "fundsLentInCountry": 100000 + idx,
            "country_latitude": 0.0,
            "country_longitude": 0.0,
            "description": f"She has operated her family business for {idx + 2} years and needs support.",
            "whySpecial": "It serves an underserved community.",
            "image_url": "https://example.test/image.webp",
            "disbursalDate": (posted - pd.Timedelta(days=7)).isoformat(),
            "fundraisingDate": posted.isoformat(),
            "raisedDate": (posted + pd.Timedelta(hours=12 + idx * 8)).isoformat(),
        })
    return pd.DataFrame(rows)


# --- Task 5: explanatory (statsmodels) fixture -----------------------------
#
# The OLS/GLM design matrices in src/statistical_analysis.py use
# C(gender_classification), C(repaymentInterval), C(sector), C(region_group),
# C(analysis_period), C(loan_size_band), and pre-specified segment
# interactions (see DEFAULT_SEGMENT_INTERACTIONS). That needs many more rows
# and much more categorical/text
# variety than `synthetic_kiva_df` provides, or the design matrix ends up
# rank-deficient (too many dummy columns relative to rows, or a categorical
# combination with no observations). `synthetic_kiva_df` is left untouched
# for Tasks 1-4; this is a separate, independent fixture.
#
# Every row gets a positive `raisedDate - fundraisingDate` duration, so the
# whole fixture is a valid completed outcome (`valid_completed_outcome` is
# True and `funded_within_24h` is never null for any row) - this lets tests
# assert `n_duration == n_binary == len(large_synthetic_kiva_df)`.
_LARGE_FIXTURE_SECTORS = ["Agriculture", "Retail", "Food", "Services", "Education", "Health"]
_LARGE_FIXTURE_REGIONS = ["Africa", "Asia", "Latin America", "Eastern Europe", "Pacific"]
_LARGE_FIXTURE_REPAYMENT_INTERVALS = ["monthly", "irregularly", "at_end"]
_LARGE_FIXTURE_GENDER_TOKENS = ["female", "male", "female, male", None]
_LARGE_FIXTURE_YEARS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
_LARGE_FIXTURE_COUNTRIES = [
    ("KE", "Kenya"), ("PH", "Philippines"), ("UG", "Uganda"), ("PE", "Peru"),
]
_LARGE_FIXTURE_THEME_SENTENCES = [
    "She runs a small retail shop selling vegetables and household goods in her community.",
    "He supports his wife and children, and hopes to send his daughter to school this year.",
    "This is an urgent request; the family needs emergency funds immediately for medical care.",
    "As a hard-working and independent business owner, she manages and controls every aspect of her shop.",
    "We are deeply grateful and thankful for the support of lenders who believe in our family business.",
    "The clean water and sanitary toilet facilities will greatly improve the health of the household.",
    "For the past several years he has been building his farming business, investing in seeds and tools.",
    "Her mother and father raised five children in this rural village near the market.",
    "They plan to buy more stock and expand their small store to serve more customers.",
    "I am responsible for my family and determined to grow this business on my own.",
]
_LARGE_FIXTURE_SHORT_HOURS = [3, 6, 10, 14, 20]
_LARGE_FIXTURE_LONG_HOURS = [30, 48, 72, 96, 130, 168, 220]


@pytest.fixture
def large_synthetic_kiva_df():
    rng = random.Random(20260817)
    rows = []
    n_rows = 120
    for idx in range(n_rows):
        year = rng.choice(_LARGE_FIXTURE_YEARS)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        posted = pd.Timestamp(year=year, month=month, day=day, tz="UTC")
        hours = (
            rng.choice(_LARGE_FIXTURE_SHORT_HOURS) if rng.random() < 0.4
            else rng.choice(_LARGE_FIXTURE_LONG_HOURS)
        )
        n_sentences = rng.randint(2, 5)
        description = " ".join(rng.sample(_LARGE_FIXTURE_THEME_SENTENCES, n_sentences))
        country_iso, country_name = rng.choice(_LARGE_FIXTURE_COUNTRIES)

        rows.append({
            "id": idx + 1,
            "status": "funded",
            "borrowerCount": rng.choice([1, 1, 1, 2, 3]),
            "name": f"Borrower {idx}",
            "gender": rng.choice(_LARGE_FIXTURE_GENDER_TOKENS),
            "loanAmount": float(rng.randint(100, 3000)),
            "lenderRepaymentTerm": rng.randint(3, 36),
            "repaymentInterval": rng.choice(_LARGE_FIXTURE_REPAYMENT_INTERVALS),
            "sector": rng.choice(_LARGE_FIXTURE_SECTORS),
            "activity": "General",
            "use": "to buy stock and materials for the business",
            "city": "Test City",
            "latitude": 0.0,
            "longitude": 0.0,
            "country_iso": country_iso,
            "country_name": country_name,
            "region": rng.choice(_LARGE_FIXTURE_REGIONS),
            "country_ppp": float(rng.randint(1000, 15000)),
            "fundsLentInCountry": rng.randint(50000, 500000),
            "country_latitude": 0.0,
            "country_longitude": 0.0,
            "description": description,
            "whySpecial": "It serves an underserved community.",
            "image_url": "https://example.test/image.webp",
            "disbursalDate": (posted - pd.Timedelta(days=7)).isoformat(),
            "fundraisingDate": posted.isoformat(),
            "raisedDate": (posted + pd.Timedelta(hours=hours)).isoformat(),
        })
    return pd.DataFrame(rows)


# `separated_binary_kiva_df` reuses `large_synthetic_kiva_df`'s generator
# with two changes, both needed to reliably reproduce genuine quasi-complete
# separation (verified empirically, not assumed) against the project's
# actual default formula:
#   1. A wider sector list (11 categories, matching the real project
#      sample's higher categorical cardinality) with a single row forced
#      into a sector ("Health") that always funds within 24 hours - one
#      perfectly-separated observation is enough to make that sector's
#      coefficient diverge and its HC3 standard errors non-finite.
#   2. A smaller sample (60 rows, vs. 120) so that one categorical level is
#      not diluted into statistical irrelevance by many competing rows.
# `log_funding_speed` (continuous) is unaffected by which sector a row is
# in, so the duration OLS model still fits normally on the same rows - only
# the 24-hour binomial GLM is driven non-finite. This reproduces,
# deterministically and offline, the real project sample's failure mode
# (sparse sector/region cells with a constant 24-hour outcome) so
# `fit_explanatory_models`'s per-model graceful-degradation path is
# exercised with genuine statistical behavior, not a mock.
_SEPARATED_FIXTURE_SECTORS = _LARGE_FIXTURE_SECTORS + [
    "Arts", "Construction", "Manufacturing", "Transportation", "Wholesale",
]
_SEPARATED_FIXTURE_REGIONS = _LARGE_FIXTURE_REGIONS + ["Middle East"]


@pytest.fixture
def separated_binary_kiva_df():
    rng = random.Random(20260817)
    rows = []
    n_rows = 60
    for idx in range(n_rows):
        year = rng.choice(_LARGE_FIXTURE_YEARS)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        posted = pd.Timestamp(year=year, month=month, day=day, tz="UTC")
        sector = rng.choice(_SEPARATED_FIXTURE_SECTORS)
        if idx == 0:
            sector = "Health"
            hours = rng.choice(_LARGE_FIXTURE_SHORT_HOURS)
        else:
            hours = (
                rng.choice(_LARGE_FIXTURE_SHORT_HOURS) if rng.random() < 0.4
                else rng.choice(_LARGE_FIXTURE_LONG_HOURS)
            )
        n_sentences = rng.randint(2, 5)
        description = " ".join(rng.sample(_LARGE_FIXTURE_THEME_SENTENCES, n_sentences))
        country_iso, country_name = rng.choice(_LARGE_FIXTURE_COUNTRIES)

        rows.append({
            "id": idx + 1,
            "status": "funded",
            "borrowerCount": rng.choice([1, 1, 1, 2, 3]),
            "name": f"Borrower {idx}",
            "gender": rng.choice(_LARGE_FIXTURE_GENDER_TOKENS),
            "loanAmount": float(rng.randint(100, 3000)),
            "lenderRepaymentTerm": rng.randint(3, 36),
            "repaymentInterval": rng.choice(_LARGE_FIXTURE_REPAYMENT_INTERVALS),
            "sector": sector,
            "activity": "General",
            "use": "to buy stock and materials for the business",
            "city": "Test City",
            "latitude": 0.0,
            "longitude": 0.0,
            "country_iso": country_iso,
            "country_name": country_name,
            "region": rng.choice(_SEPARATED_FIXTURE_REGIONS),
            "country_ppp": float(rng.randint(1000, 15000)),
            "fundsLentInCountry": rng.randint(50000, 500000),
            "country_latitude": 0.0,
            "country_longitude": 0.0,
            "description": description,
            "whySpecial": "It serves an underserved community.",
            "image_url": "https://example.test/image.webp",
            "disbursalDate": (posted - pd.Timedelta(days=7)).isoformat(),
            "fundraisingDate": posted.isoformat(),
            "raisedDate": (posted + pd.Timedelta(hours=hours)).isoformat(),
        })
    return pd.DataFrame(rows)
