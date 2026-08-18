from pathlib import Path


def test_notebook_script_has_portable_paths_and_no_duplicated_legacy_modeling():
    text = Path("notebooks/starter_eda.py").read_text(encoding="utf-8")
    assert "F:/" not in text
    assert 'pkl_path = "../data/' not in text
    assert "train_test_split" not in text
    assert "run_analysis" in text
    assert "analysis_period" in text
