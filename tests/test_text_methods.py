from pathlib import Path

from src.text_methods import build, entry_count

ROOT = Path(__file__).resolve().parents[1]


def test_entry_count_counts_only_top_level_alternatives():
    assert entry_count(r"\b(?:child(?:ren)?|family|stud(?:y|ies))\b") == 3


def test_inventory_matches_the_code_settings():
    out = build()
    assert set(out['word_list_entries']) == {'family', 'basic_needs', 'business', 'agency', 'gratitude', 'urgency',
                                             'first_person', 'third_person'}
    assert out['word_list_entries']['first_person'] == 8
    assert out['tfidf'] == {'max_features': 5000, 'min_df': 5, 'ngram_range': [1, 2], 'sublinear_tf': True}
    assert out['compressed_components'] == 64


def test_topic_settings_still_match_the_notebook():
    source = (ROOT / 'notebooks/1_full_dataset_eda.py').read_text()
    topics = build()['topics']
    assert f"N_TOPICS = {topics['themes']}" in source
    assert f"max_features={topics['max_features']}" in source and 'min_df=5' in source
    assert 'valid.sample(min(20_000' in source and topics['sample'] == 20000
