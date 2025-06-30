"""
test_core.py - Unit tests for core.py in the Global Culture Project pipeline.
"""
import os
import tempfile
import shutil
import pandas as pd
import pytest
from core import (
    process_file,
    postprocess_segments,
    export_segments_csv,
    export_segments_markdown,
    export_segments_per_markdown,
    update_repo_csv,
    detect_duplicates,
    filter_segments,
    get_flagged_segments,
)

def make_dummy_segments():
    return [
        {
            'title': 'Culture A',
            'content': 'This is content for A.',
            'summary': 'Summary A',
            'tags': 'tag1,tag2',
            'confidence_score': 'high',
        },
        {
            'title': 'Culture B',
            'content': 'This is content for B.',
            'summary': 'Summary B',
            'tags': '',
            'confidence_score': 'low',
        },
        {
            'title': 'Culture A',
            'content': 'Duplicate title.',
            'summary': 'Summary C',
            'tags': 'tag3',
            'confidence_score': 'medium',
        },
    ]

def test_postprocess_segments_adds_flags():
    segs = make_dummy_segments()
    processed = postprocess_segments(segs)
    assert all('segment_id' in s for s in processed)
    assert any(s['needs_attention'] for s in processed)

def test_detect_duplicates():
    segs = make_dummy_segments()
    dups = detect_duplicates(segs)
    assert 'Culture A' in dups
    assert 'Culture B' not in dups

def test_filter_segments():
    segs = make_dummy_segments()
    filtered = filter_segments(segs, 'A')
    assert all('A' in s['title'] for s in filtered)

def test_get_flagged_segments():
    segs = make_dummy_segments()
    flagged = get_flagged_segments(postprocess_segments(segs))
    assert any(flagged)

def test_export_and_update_repo_csv():
    segs = postprocess_segments(make_dummy_segments())
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, 'out.csv')
        export_segments_csv(segs, csv_path)
        assert os.path.exists(csv_path)
        df = pd.read_csv(csv_path)
        assert len(df) == len(segs)
        # Test repo update
        repo_path = os.path.join(tmpdir, 'repo.csv')
        update_repo_csv(segs, repo_path)
        assert os.path.exists(repo_path)
        repo_df = pd.read_csv(repo_path)
        assert len(repo_df) == len(segs)

def test_export_segments_markdown_and_per_markdown():
    segs = postprocess_segments(make_dummy_segments())
    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = os.path.join(tmpdir, 'out.md')
        export_segments_markdown(segs, md_path)
        assert os.path.exists(md_path)
        md_dir = os.path.join(tmpdir, 'mds')
        export_segments_per_markdown(segs, md_dir)
        files = os.listdir(md_dir)
        assert len(files) == len(segs)

def test_process_file():
    # This test assumes a sample.txt exists in input_docs/ with at least one segmentable entry
    from core import process_file
    path = "input_docs/sample.txt"
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("Testland\nThis is a test segment.")
    segs = process_file(path, use_gpt=False)
    assert len(segs) > 0
    assert "title" in segs[0]
    assert "content" in segs[0]

def test_postprocess():
    from core import postprocess_segments
    fake = [{'title': 'TESTLAND', 'content': 'Short.', 'summary': 'Brief summary...'}]
    flagged = postprocess_segments(fake)
    assert flagged[0]['needs_attention'] is True
