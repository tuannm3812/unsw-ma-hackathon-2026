#!/usr/bin/env python3
"""
Update Google Slides presentation directly via gslides CLI.
Applies verified errata from docs/presentation/archive/september_prep/deck_edit_list.md to
the duplicated Google Slides deck.
"""
import subprocess
import json
import sys

PRES_ID = "17rHwKFXiqN4GBo8TT5xnBWk33bN7niIodw9K9APNwDk"

def get_slide_page(pres_id, slide_id):
    res = subprocess.run(
        ["gslides", "readonly", "get-page", pres_id, slide_id, "--json"],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(res.stdout)

def update_element_text(pres_id, element_id, new_text):
    print(f"Updating element {element_id}...")
    res = subprocess.run(
        ["gslides", "mutate", "update-text", pres_id, "--element", element_id, "--text", new_text],
        capture_output=True,
        text=True
    )
    if res.returncode != 0:
        print(f"Error updating {element_id}: {res.stderr}")
        return False
    print(f"  Successfully updated {element_id}")
    return True

def main():
    print(f"Starting live Google Slides update on presentation: {PRES_ID}")
    
    # 1. Slide 1 (Cover): Add data line
    # Element: g3faff9733a3_0_547
    cover_text = "Team Cultural Blend\nUniversity of Technology Sydney\nKiva loan data · 1.45 million real loans · 2016–2025"
    update_element_text(PRES_ID, "g3faff9733a3_0_547", cover_text)

    # 2. Slide 3 (Method): Exact 64/120 figure and few-cluster screen
    # Element: g3faff9733a3_0_623
    slide3_text = (
        "Predictive claims: trained only on the past, tested only on loans posted 2024–2025. No peeking at the future.\n"
        "Framing claims: Every \"significant\" framing result went through two more tests, standard errors clustered by country, "
        "then a stricter few-cluster screen where it rested on a handful of countries.\n"
        "Across both explanatory models, 64 of 120 significant coefficients did not survive the country-clustered re-test. "
        "That is the point of the method.\n"
        "SHAP importance shown as complementary predictive evidence only. It cannot confirm or refute a statistical finding."
    )
    update_element_text(PRES_ID, "g3faff9733a3_0_623", slide3_text)

    # 3. Slide 4 (Market): Headline, number strip, and sample persistence bullet
    update_element_text(
        PRES_ID,
        "g3faff9733a3_0_628",
        "A slower market is the operating reality — and it is partner capital that waits."
    )
    update_element_text(
        PRES_ID,
        "g3faff9733a3_0_630",
        "46.0% → 30.3% → 30.0%  funded within 24 hours"
    )
    slide4_bullets = (
        "Pre-pandemic, almost half of all loans funded within a day.\n"
        "Since 2020: under a third — and four years on, still not recovered. "
        "Partner capital now waits longer, not the borrower: 96% of loans are already disbursed before the page goes live.\n"
        "589,823 loans before vs 565,474 after — not a thin sample, and the slowdown persists to date."
    )
    update_element_text(PRES_ID, "g3faff9733a3_0_631", slide4_bullets)

    # 4. Slide 5 (Structure): Women/men phrasing and country spread
    update_element_text(
        PRES_ID,
        "g3faff9733a3_0_648",
        "Loans posted by women fund in a median 2.3 days; by men, 7.7"
    )
    slide5_bullets = (
        "Loan amount + repayment terms: linked to funding speed ~10× more strongly than any single narrative choice. "
        "Bigger ask, longer on the platform.\n"
        "Sector alone spans well over an order of magnitude in speed; country gaps are wider still — 0.2 to 20.5 days.\n"
        "These spreads are associations, not causes."
    )
    update_element_text(PRES_ID, "g3faff9733a3_0_649", slide5_bullets)

    # 5. Slide 6 (Scrutiny): Headline and authoritative urgency p-value (p ≈ 0.49)
    update_element_text(
        PRES_ID,
        "g3faff9733a3_0_654",
        "Storytelling coaching: no robust evidence it moves the needle."
    )
    slide6_bullets = (
        "Urgency: looked universal (p<0.001) — collapses under country clustering (p≈0.49). Not recommended.\n"
        "Family: corrected test → Middle East (Palestine+Yemen) & Central America (Honduras+Nicaragua) same direction in every fit — "
        "but 2 countries each; few-cluster t(1) screen bar is 12.7, not 1.96: p≈0.06–0.21. A hypothesis, not a finding.\n"
        "Sentiment: positive tone ↔ slower funding, but significance flips between specifications — genuinely open.\n"
        "SHAP: no family / agency / urgency feature in the model's top 15 ⇒ complementary evidence, not confirmation."
    )
    update_element_text(PRES_ID, "g3faff9733a3_0_657", slide6_bullets)

    # 6. Slide 7 (Topics): Callout and notes phrasing
    update_element_text(
        PRES_ID,
        "g3faff9733a3_0_664",
        "From   1.5 days\nTo     13.5 days\nacross story topics — a ninefold swing"
    )
    update_element_text(
        PRES_ID,
        "g3fb003f72f8_0_899",
        "Notes: Water and sanitation stories fund in under 2 days; group farming loans take ~2 weeks to fund - themes track what the loan is FOR."
    )

    # 7. Slide 8 (Recommendations): Title, grammar, double space
    update_element_text(
        PRES_ID,
        "g3f9f6b39b41_0_9",
        "What this means in practice for the Kiva team"
    )
    update_element_text(
        PRES_ID,
        "g3f9f6b39b41_0_26",
        "DO review the structural gaps (programme / sector / region / gender) — they are ~10x the size of any wording effect."
    )
    slide8_card4 = (
        "PROTOTYPE, then re-validate: the 24h classifier ranks well among eventually-funded loans "
        "(AUC ≈ 0.90, strictly future data), but expired/withdrawn listings aren't in the data, "
        "so an early warning flag first needs all posted listings, a defined target, and retraining on that population."
    )
    update_element_text(PRES_ID, "g3f9f6b39b41_0_27", slide8_card4)

    # 8. Slide 11 (Closing): Refined quote
    update_element_text(
        PRES_ID,
        "g3fb003f72f8_0_9",
        "“In this data, the story barely registers.\nThe structure carries the signal.”"
    )

    print("\nAll live edits completed successfully on Google Slides!")

if __name__ == "__main__":
    main()
