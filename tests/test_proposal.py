import re
from pathlib import Path


def _proposal_text():
    return Path("proposal/proposal.md").read_text(encoding="utf-8")


def test_proposal_contains_required_sections():
    text = _proposal_text()
    for heading in [
        "# Beyond a Good Story",
        "## Project Aim and Research Questions",
        "## Proposed Analytical Approaches",
        "## Data Items to Be Used",
        "## Expected Outcomes and Managerial Relevance",
        "## References",
    ]:
        assert heading in text


def test_proposal_is_within_1500_words_excluding_references():
    body = _proposal_text().split("## References", 1)[0]
    words = re.findall(r"\b[\w’'-]+\b", body)
    assert len(words) <= 1500


def test_proposal_does_not_make_causal_or_completed_analysis_claims():
    body = _proposal_text().lower()
    assert "will cause" not in body
    assert "proves that" not in body
    assert "our results show" not in body
