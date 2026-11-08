from src.clustering_split import split

SAMPLE = """Cluster-Robust Sensitivity Check
====
Duration model (log funding speed):
  - C(sector)[T.Food]: HC3 p=0.0000 (significant); clustered p=0.2165 (not significant) [CONCLUSION CHANGES]
  - family_mentions_per_100_words:C(region_group)[T.Asia]: HC3 p=0.0000 (significant); clustered p=0.3 (not significant) [CONCLUSION CHANGES]
  - urgency_mentions_per_100_words: HC3 p=0.0000 (significant); clustered p=0.0100 (significant) [same conclusion]
24-hour model (logistic):
  - agency_mentions_per_100_words: HC3 p=0.2000 (not significant); clustered p=0.4 (not significant) [same conclusion]
Average Within-Region Family-Framing Slopes
"""


def test_split_counts_text_interactions_as_text():
    result = split(SAMPLE)
    duration = result['models']['Duration model (log funding speed)']
    assert duration['text'] == {'tested': 2, 'significant': 2, 'lost': 1}
    assert duration['control'] == {'tested': 1, 'significant': 1, 'lost': 1}
    assert result['total']['text']['tested'] == 3
