import pandas as pd

from src.text_placebo import shuffle_within


def test_shuffle_stays_within_strata_and_keeps_rows_together():
    frame = pd.DataFrame({'k': list('aaaabbbb'), 'x': range(8), 'y': [v * 10 for v in range(8)]})
    out, moved = shuffle_within(frame, ['x', 'y'], ['k'], seed=1)
    assert sorted(out.loc[out.k == 'a', 'x']) == [0, 1, 2, 3]
    assert sorted(out.loc[out.k == 'b', 'x']) == [4, 5, 6, 7]
    assert (out['y'] == out['x'] * 10).all()   # columns move jointly
    assert 0 < moved <= 1
    assert frame['x'].tolist() == list(range(8))   # input untouched
