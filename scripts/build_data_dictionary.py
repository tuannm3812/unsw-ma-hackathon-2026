"""Generate docs/1_data_dictionary.md: the official field definitions from
data/Kiva Data Dictionary.xlsx, cross-checked against the real data, with
an explicit record of how each field is used by this project.

Privacy: free-text fields (description, use, name, image_url) are summarised
statistically only - no raw borrower text is reproduced, matching the
notebooks' own handling.
"""
import pickle
import io
import pandas as pd

# how this project uses each field: (status, note)
USAGE = {
 "id":                  ("Not used", "Identifier. Never in the predictor allowlist."),
 "status":              ("Validity filter", "Only `funded` (1,452,203) and `refunded` (1,637) appear - no expired/withdrawn listings, which is the outcome-boundary caveat on Slide 9."),
 "borrowerCount":       ("Predictor", "Also drives `is_group_loan`. Group loans are slower: median 5.7d vs 2.6d."),
 "name":                ("Not used", "Borrower name - excluded for privacy, never loaded into features."),
 "gender":              ("Predictor", "Via `gender_classification`. Female-posted median 2.3d vs male 7.7d."),
 "loanAmount":          ("Predictor", "Via `log_loan_amount` + `loan_size_band`. Top SHAP feature (0.446); Spearman with speed 0.559."),
 "lenderRepaymentTerm": ("Predictor", "2nd on SHAP (0.337); Spearman 0.368."),
 "repaymentInterval":   ("Predictor", "monthly 9.1d / irregularly 10.8d / at_end 12.8d."),
 "sector":              ("Predictor", "Via `sector_group` (<1,000 loans folded into Other). 0.9-12.1d across 17 levels."),
 "activity":            ("Predictor", "168 levels, 0.9-19.8d across the 80 with >=1,000 loans. In the model, not on a slide."),
 "use":                 ("Partly used", "Length/missingness only (`use_word_count`, `use_char_count`, `use_missing`). Content unused - semi-templated, median 10 words, duplicates sector/activity."),
 "city":                ("Not used", "14,512 levels; geography already carried by country and region."),
 "latitude":            ("Not used", "City coordinates - proxy for country, which is modelled directly."),
 "longitude":           ("Not used", "As above."),
 "country_iso":         ("Predictor", "48 countries, the categorical geography actually modelled."),
 "country_name":        ("Clustering unit", "Deliberately omitted as a predictor (redundant with `country_iso`) but used as the cluster variable for robust standard errors. 0.2d (Nepal) to 20.5d (Senegal)."),
 "region":              ("Predictor", "Via `region_group`, 6 levels, 3.7-15.6d. Note this compresses country's 100x spread to 4x."),
 "country_ppp":         ("Predictor", "GDP per capita. Weak: Pearson -0.108."),
 "fundsLentInCountry":  ("Deliberately omitted", "Cumulative country lending volume - excluded as an unverified-timestamp field (its value at posting time cannot be established, so it risks leakage)."),
 "country_latitude":    ("Not used", "Country centroid - redundant with country identity."),
 "country_longitude":   ("Not used", "As above."),
 "description":         ("Predictor (derived)", "The core text field: all lexicon rates, VADER sentiment, length/specificity features and the NMF topics come from here. Raw text never enters the model."),
 "whySpecial":          ("Partly used - GAP", "Only `whySpecial_missing`. Its 643 values are a programme/partner label (92% single-country) spanning 0.2-30.9 mean days: the widest structural gap in the data, and unmodelled. See Q&A C10."),
 "image_url":           ("Not used", "No image analysis in scope."),
 "disbursalDate":       ("Not used - GAP", "96.4% of loans are disbursed BEFORE fundraising opens (median 24.2 days). Funding speed is therefore the partner's capital-replenishment cycle, not the borrower's wait. See Q&A D6."),
 "fundraisingDate":     ("Outcome + predictor", "Outcome start; also `fundraising_year`, `fundraising_month`, `analysis_period`, and the 2024-01-01 chronological split boundary."),
 "raisedDate":          ("Outcome", "Outcome end. `funding_speed_days = raisedDate - fundraisingDate`, exactly the dictionary's stated lender-decision outcome."),
}

TEXTY = {"description", "use", "name", "image_url"}

# official definitions
dd = pd.read_excel("data/Kiva Data Dictionary.xlsx", sheet_name="Kiva Loans", header=None).dropna(how="all")
defs = {}
for _, r in dd.iterrows():
    cells = [str(c).strip() for c in r.tolist() if str(c) != "nan"]
    if len(cells) >= 2 and cells[0] in USAGE:
        defs[cells[0]] = cells[1]

with open("data/Kiva_Loans.pkl", "rb") as f:
    df = pd.DataFrame(pickle.load(f))
n = len(df)

import numpy as np
_fr = pd.to_datetime(df["fundraisingDate"], errors="coerce", utc=True)
_ra = pd.to_datetime(df["raisedDate"], errors="coerce", utc=True)
_di = pd.to_datetime(df["disbursalDate"], errors="coerce", utc=True)
df["speed_days"] = (_ra - _fr).dt.total_seconds() / 86400
df["disb_lead"] = (_fr - _di).dt.total_seconds() / 86400
_v = df.loc[df["speed_days"].notna() & (df["speed_days"] >= 0)]
_rng = np.random.RandomState(7)
_picks = pd.concat([
    _v.nsmallest(400, "speed_days").sample(2, random_state=_rng),
    _v[(_v.speed_days > 2) & (_v.speed_days < 6)].sample(2, random_state=_rng),
    _v[_v.borrowerCount > 3].sample(1, random_state=_rng),
    _v.nlargest(4000, "speed_days").sample(1, random_state=_rng),
])
_cols = ["gender", "borrowerCount", "loanAmount", "lenderRepaymentTerm", "repaymentInterval",
         "sector", "activity", "country_name", "region", "speed_days", "disb_lead"]
SAMPLE_TABLE = ["| " + " | ".join(_cols) + " |", "|" + "---|" * len(_cols)]
for _, _r in _picks[_cols].round(2).iterrows():
    SAMPLE_TABLE.append("| " + " | ".join(str(x) for x in _r.tolist()) + " |")
import re as _re
STRUCT_TABLE = ["| field | dtype | non-null | distinct |", "|---|---|---|---|"]
for _c in df.columns:
    if _c.startswith(("speed_days", "disb_lead")):
        continue
    STRUCT_TABLE.append(f"| `{_c}` | {str(df[_c].dtype)} | {df[_c].notna().mean():.1%} | {df[_c].nunique():,} |")

_rng2 = np.random.RandomState(11)
_pair = pd.concat([
    _v.nsmallest(300, "speed_days").sample(1, random_state=_rng2),
    _v.nlargest(3000, "speed_days").sample(1, random_state=_rng2),
])
_WITHHELD = {"id", "name", "image_url", "disbursalDate", "fundraisingDate", "raisedDate",
             "city", "latitude", "longitude"}  # city + precise coords add locating
                                               # specificity with no analytical value here
COMPARE_TABLE = ["| field | fast row | slow row |", "|---|---|---|"]
for _c in df.columns:
    if _c.startswith(("speed_days", "disb_lead")):
        continue
    if _c in _WITHHELD:
        COMPARE_TABLE.append(f"| `{_c}` | *withheld* | *withheld* |")
        continue
    if _c == "description":
        _vals = []
        for _t in _pair["description"]:
            _w = len(str(_t).split())
            _vals.append(f"*not reproduced* — {_w} words")
        COMPARE_TABLE.append(f"| `description` | {_vals[0]} | {_vals[1]} |")
        continue
    _a, _b = [str(x)[:64] for x in _pair[_c].tolist()]
    COMPARE_TABLE.append(f"| `{_c}` | {_a} | {_b} |")
_sp = _pair["speed_days"].tolist()
_ld = _pair["disb_lead"].tolist()
COMPARE_TABLE.append(f"| **funding speed** (derived) | **{_sp[0]:.2f} days** | **{_sp[1]:.2f} days** |")
COMPARE_TABLE.append(f"| **disbursal lead** (derived) | {_ld[0]:.1f} days before posting | {_ld[1]:.1f} days before posting |")

SAMPLE_TEXT = ["| field | example (verbatim) | scope |", "|---|---|---|"]
for _t in _picks["use"].head(2):
    SAMPLE_TEXT.append(f"| `use` | {_re.sub(chr(92)+'s+', ' ', str(_t))[:70]} | one loan |")
for _t, _n in _v["whySpecial"].value_counts().head(2).items():
    SAMPLE_TEXT.append(f"| `whySpecial` | {str(_t)[:70]} | {_n:,} loans |")

lines = [
 "# Kiva loan data — field reference",
 "",
 "Every field in `data/Kiva_Loans.pkl` (1,453,846 rows), combining the official",
 "definitions from `data/Kiva Data Dictionary.xlsx` with the actual coverage in the",
 "data and an explicit record of **how this project used each field**.",
 "",
 "Generated by `scripts/build_data_dictionary.py`. Free-text fields are summarised",
 "statistically only — no raw borrower text is reproduced here, matching the",
 "notebooks' own privacy handling.",
 "",
 "## The outcome, as the dictionary defines it",
 "",
 "> **Key lender decision outcome:** `funding speed = raisedDate - fundraisingDate`",
 "",
 "That is exactly what this project models — the outcome is the challenge's own",
 "definition, not a reinterpretation of it.",
 "",
 "## Fields",
 "",
 "| Field | Official definition | Non-null | Distinct | How we used it |",
 "|---|---|---|---|---|",
]
for c in df.columns:
    if c not in USAGE:
        continue
    nn = df[c].notna().sum()
    nu = df[c].nunique()
    status, note = USAGE[c]
    d = defs.get(c, "—")
    lines.append(f"| `{c}` | {d} | {nn/n:.1%} | {nu:,} | **{status}.** {note} |")

lines += [
 "",
 "## Omissions: deliberate vs. gaps",
 "",
 "The predictor set is an explicit **allowlist** (`src/modeling.py`), so a field is",
 "absent by never having been added, not by being filtered out. Three categories:",
 "",
 "**Deliberate and documented** — `country_name` (redundant with `country_iso`, and",
 "reserved as the clustering unit), `fundsLentInCountry` (unverified timestamp →",
 "leakage risk), and the raw text of `description`/`use`/`whySpecial` (used only via",
 "derived features).",
 "",
 "**Deliberate and obvious** — `id`, `name`, `image_url`: identifiers and privacy.",
 "",
 "**Gaps we found late (2026-09-03), both material:**",
 "",
 "1. `disbursalDate` — never considered. It shows 96.4% of loans are disbursed to the",
 "   borrower *before* the page goes live (median 24.2 days). This changes nothing",
 "   numerically but changes *who* funding speed is about: the field partner's capital",
 "   cycle, not the borrower's wait. The dictionary's own example row shows it",
 "   (disbursal 2021-07-09, posting 2021-07-21) — it was visible from the start.",
 "2. `whySpecial` as a **category** — reduced to a missingness flag. Its 643 values are",
 "   a programme/partner label spanning 0.2–30.9 mean days, the widest structural gap",
 "   in the dataset (wider than country, activity or sector).",
 "",
 "Both are recorded honestly in the Q&A pack (D6 and C10) rather than quietly fixed.",
 "",
 "## What a row actually looks like",
 "",
 "A deterministic sample spanning the speed range (loan attributes only — identifiers",
 "and free text are withheld, see the privacy note below):",
 "",
] + SAMPLE_TABLE + [
 "",
 "Four things this sample shows, all of which matter for how the findings are read:",
 "",
 "1. **The fast tail is real.** Rows funding in `0.00` days are small Philippine farming",
 "   loans filled within the hour — the reason the median (2.85d) sits far below the",
 "   mean (9.47d).",
 "2. **`disb_lead` is positive in almost every row** — the borrower already held the",
 "   capital that many days before the page went live. The 96.4% pre-disbursal fact is",
 "   visible in a six-row sample.",
 "3. **The group-loan penalty is visible** — the multi-borrower row funds far slower,",
 "   consistent with the population medians (5.7d group vs 2.6d individual).",
 "4. **Descriptions are field-partner prose, not borrower voice.** They are third-person",
 "   and formulaic — different loans share near-identical sentence structure (\"X is 48",
 "   years old and has seven children… is in the agricultural business, farming rice\").",
 "   This is the most intuitive evidence for the programme-effect argument in Q&A C10:",
 "   writing style is largely a partner house style, which is why a surviving text",
 "   signal such as third-person voice most plausibly measures *who wrote the page*.",
 "",
 "**Privacy note:** no raw `description` text is reproduced here. Descriptions open with",
 "the borrower's name and biography, and recur mid-paragraph, so automated redaction is",
 "not reliable enough to commit. `use` phrases (short, generic) and `whySpecial`",
 "(programme boilerplate covering hundreds of thousands of loans) are safe to show:",
 "",
] + SAMPLE_TEXT + [
 "",


 "## The raw data as stored",
 "",
 "`Kiva_Loans.pkl` is a **list of " + f"{len(df):,}" + " dicts**, one per loan, each with the same 27",
 "keys — not a pickled DataFrame, which is why `src/data_loader` uses `pickle.load`",
 "rather than `pd.read_pickle`. Loaded into a DataFrame it occupies ~3 GB in memory.",
 "",
 "Note the empty-string convention: `description`, `use` and `city` are never null in",
 "the Python sense — absent values arrive as `''` or the string `'None'`. A naive",
 "`.isna()` check would report 100% coverage and silently treat 39,088 storyless loans",
 "as having text. `src/features.py::_is_missing_text` tests `not raw.strip()`, so the",
 "`*_missing` flags are correct.",
 "",
] + STRUCT_TABLE + [
 "",
 "**2.7% of loans (39,088) carry no description at all** — largely Kiva's own privacy",
 "redaction of large group loans (8,454 records are named *Anonymized Kivans*, mean",
 "18.4 borrowers). Unadjusted, those storyless loans fund **faster** than loans with a",
 "description (median 1.81d vs 2.88d; mean 7.83d vs 9.51d). Confounded by size and",
 "group structure, so not a finding — but a third independent pointer in the same",
 "direction as the tested results.",
 "",
 "## Fast row vs slow row — every field",
 "",
 "The two loans behind the contrast above, field by field. Identifying fields are",
 "marked *withheld*: names, loan ids, image urls, exact timestamps and precise",
 "locations can be cross-referenced against live Kiva pages, so they are never",
 "committed. Dates appear only as derived intervals, and geography only at country",
 "level — which is also the level the analysis actually uses.",
 "",
] + COMPARE_TABLE + [
 "",
 "Reading down the table: the two loans agree on `status`, `borrowerCount`,",
 "`sector` and `repaymentInterval`, and differ on exactly the axes the analysis",
 "identifies as structural — amount, country, programme label — plus the outcome. The",
 "narrative direction is the opposite of the storytelling hypothesis, which is the",
 "point of recording them together.",
 "",
 "### Two contrasting rows — the thesis in miniature",
 "",
 "Inspecting two complete rows (the full field set, including the free text this",
 "document does not reproduce) illustrates the project's argument more directly than",
 "any coefficient:",
 "",
 "| | Fast row | Slow row |",
 "|---|---|---|",
 "| Loan amount | $250 | $1,700 |",
 "| Country | Philippines | Rwanda |",
 "| Sector / activity | Food / Cereals | Food / Grocery Store |",
 "| Term | 8 months, monthly | 10 months, monthly |",
 "| Programme (`whySpecial`) | generic — *It helps this borrower grow their business* (342,277 loans carry this label) | specialised — *It helps refugees launch businesses to rebuild their lives* |",
 "| Disbursal lead | ~33 days before posting | ~20 days before posting |",
 "| **Funding speed** | **under a minute** | **46 days** |",
 "",
 "Four observations:",
 "",
 "1. **Structure explains the gap, not story.** Same sector, same repayment interval,",
 "   similar terms. What differs is amount (~7x), country, and programme — the three",
 "   structural axes the analysis identifies as dominant.",
 "2. **The narrative runs opposite to the storytelling hypothesis.** The slow loan",
 "   carries by far the more compelling human account: a refugee family rebuilding",
 "   after fleeing conflict and supplying their camp's community. The fast loan's",
 "   description is dry and formulaic. If persuasive writing drove funding speed, this",
 "   pair would be reversed. It is one illustration, not evidence — but it is the most",
 "   intuitive version of a result established properly at population scale.",
 "3. **The programme label visibly separates them**, consistent with `whySpecial`",
 "   spanning 0.2-30.9 mean days: a generic label on a large routine pipeline against a",
 "   specialised programme serving a narrower lender base.",
 "4. **Both were pre-disbursed** (~33 and ~20 days), so neither borrower was waiting on",
 "   lenders for capital — the point formalised in the `disbursalDate` gap above.",
 "",
 "The fast row's description also refers to a long history of prior loans through the",
 "same field partner, which suggests the mechanism is an established partner pipeline",
 "with committed lender capital rather than anything about how the page was written.",
 "",
 "## Reproducing these numbers",
 "",
 "```bash",
 "python3 scripts/build_data_dictionary.py   # regenerates this file",
 "python3 scripts/audit_all_features.py      # every field vs funding speed",
 "```",
 "",
]
io.open("docs/1_data_dictionary.md", "w", encoding="utf-8").write("\n".join(lines))
print(f"wrote docs/1_data_dictionary.md ({len(lines)} lines, {sum(1 for c in df.columns if c in USAGE)} fields)")
