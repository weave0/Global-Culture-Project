import pytest
from utils import segment_cultures

@pytest.fixture
def known_set():
    return {"JAPANESE", "FRENCH"}

def test_segment_multiple_cultures(known_set):
    text = "JAPANESE\nIntro\nDetails...\nFRENCH\nBonjour\nOui oui"
    segs = segment_cultures(text, known_set)
    assert len(segs) == 2
    assert segs[0]['title'] == "JAPANESE"
    assert segs[1]['title'] == "FRENCH"
