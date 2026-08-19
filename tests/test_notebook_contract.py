import re
from pathlib import Path


def test_notebook_script_has_portable_paths_and_no_duplicated_legacy_modeling():
    text = Path("notebooks/starter_eda.py").read_text(encoding="utf-8")
    assert "F:/" not in text
    assert 'pkl_path = "../data/' not in text
    assert "train_test_split" not in text
    assert "run_analysis" in text
    assert "analysis_period" in text


def test_notebook_public_preview_excludes_borrower_identifiers():
    # The Dataset Overview section's `preview_cols` renders actual raw
    # dataset rows for a public/Kaggle audience - unlike the schema table
    # above it (which only lists column *names* as metadata, not values).
    # Identifying columns must never appear there: this project analyzes
    # aggregate narrative/structural patterns, never individual borrowers,
    # and a public preview shouldn't redistribute identifiable rows just
    # because the source platform happens to display them. This covers
    # more than the obvious explicit-identifier columns (name/id/
    # image_url): raw description/use/whySpecial text usually opens with
    # the borrower's name and a short biography (Kiva's own narrative
    # convention), and an exact fundraisingDate/raisedDate timestamp is
    # specific enough to cross-reference a real loan on Kiva's own public
    # site - both are identifying in practice even though neither is an
    # "identifier column" by name.
    text = Path("notebooks/starter_eda.py").read_text(encoding="utf-8")
    match = re.search(r"preview_cols = \[(.*?)\]", text, re.DOTALL)
    assert match, "notebook must define preview_cols for its Dataset Overview preview"
    preview_block = match.group(1)
    forbidden_columns = (
        "name", "id", "image_url",  # explicit identifiers
        "description", "use", "whySpecial",  # free text naming the borrower
        "fundraisingDate", "raisedDate",  # exact timestamps, cross-referenceable
    )
    for column in forbidden_columns:
        assert f'"{column}"' not in preview_block, (
            f"{column!r} must not appear in the public row preview"
        )


def test_readme_documents_current_portable_workflow():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "python3 -m src.run_analysis" in text
    assert "chronological" in text.lower()
    assert "association" in text.lower()
    assert "F:/" not in text
    assert "file:///" not in text
    for module in ["text_transformer.py", "validation.py", "run_analysis.py"]:
        assert module in text
