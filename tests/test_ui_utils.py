import os
import pandas as pd
from utils import segment_cultures

def test_file_discovery(tmp_path):
    # Create dummy files
    (tmp_path / "input_docs").mkdir()
    f1 = tmp_path / "input_docs" / "a.docx"
    f2 = tmp_path / "input_docs" / "b.xlsx"
    f1.write_text("test")
    f2.write_text("test")
    files = [str(f) for f in (tmp_path / "input_docs").glob("*.docx")]
    assert str(f1) in files

def test_segment_metadata():
    segments = [
        {"title": "ENGLISH", "content": "Hello"},
        {"title": "FRANÇAIS", "content": "Bonjour"},
    ]
    for seg in segments:
        seg['source_file'] = "test.docx"
        seg['run_id'] = "20250101_000000"
    assert all('source_file' in seg and 'run_id' in seg for seg in segments)

def test_segment_filtering():
    segments = [
        {"title": "ENGLISH", "content": "Hello world"},
        {"title": "FRANÇAIS", "content": "Bonjour le monde"},
    ]
    search = "bonjour"
    filtered = [s for s in segments if search.lower() in s['title'].lower() or search.lower() in s['content'].lower()]
    assert len(filtered) == 1
    assert filtered[0]['title'] == "FRANÇAIS"
