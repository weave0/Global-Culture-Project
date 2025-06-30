import pytest
from utils import is_culture_title, segment_cultures, truncate_for_gpt, load_known_cultures

def test_is_culture_title():
    known = {"JAPANESE", "FRENCH"}
    assert is_culture_title("JAPANESE", known)
    assert is_culture_title("FRENCH", known)
    assert not is_culture_title("not a title", known)
    assert is_culture_title("SOME CULTURE", set())

def test_segment_cultures_basic():
    known = {"JAPANESE"}
    text = "JAPANESE\nOrientation\nJapan is an island nation..."
    segs = segment_cultures(text, known)
    assert segs[0]['title'] == "JAPANESE"
    assert "Japan is an island nation" in segs[0]['content']

def test_truncate_for_gpt():
    text = "a " * 2000
    truncated = truncate_for_gpt(text, enc=None, max_tokens=10)
    assert len(truncated) < len(text)

def test_load_known_cultures(tmp_path):
    f = tmp_path / "cultures.txt"
    f.write_text("JAPANESE\nFRENCH\n")
    known = load_known_cultures(str(f))
    assert "JAPANESE" in known
    assert "FRENCH" in known
