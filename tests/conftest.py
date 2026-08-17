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
