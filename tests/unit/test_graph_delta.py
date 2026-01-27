from graph.delta import compute_text_delta


def test_compute_text_delta_identical():
    assert compute_text_delta("same", "same") == []


def test_compute_text_delta_replace():
    assert compute_text_delta("abc", "adc") == [{"original": "b", "edited": "d"}]


def test_compute_text_delta_insert():
    deltas = compute_text_delta("abc", "axbc")
    assert deltas == [{"original": "", "edited": "x"}]


def test_compute_text_delta_delete():
    deltas = compute_text_delta("abc", "ac")
    assert deltas == [{"original": "b", "edited": ""}]
