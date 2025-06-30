# core.py — Central pipeline controller for cultural data ingestion and export.
#
# 🧩 Responsibilities:
# - Accepts raw cultural content from .docx/.xlsx/.txt files
# - Applies title-based segmentation (via utils.segment_cultures)
# - Optionally enriches data with GPT-generated summaries, tags
# - Adds metadata (run_id, segment_id, language detection, confidence)
# - Supports full CSV and Markdown export (merged or per-segment)
# - Updates a global repo CSV, avoids duplicates
#
# 🧪 Expects enrich_segments() and langdetect to be available but degrades gracefully if not.
# 🚀 This file should be callable by both CLI and Streamlit UI layers.

"""
core.py - Core logic for the Global Culture Project pipeline.
Handles file IO, segmentation, enrichment, validation, and export.

Field Reference (core.py segment dict fields):

| Field              | Purpose                                 |
|--------------------|-----------------------------------------|
| title              | Segment title (usually a culture name)   |
| content            | Full segment content                     |
| tags               | Enrichment tags (if GPT used)            |
| summary            | Enrichment summary (if GPT used)         |
| summary_quality_score | Optional enrichment confidence         |
| confidence_score   | Derived confidence ("high"/"medium")     |
| segment_id         | UUID to uniquely track this segment      |
| run_id             | Timestamp of run                         |
| source_file        | Name of file processed                   |
| title_lang         | Detected language of title               |
| needs_attention    | Boolean flag for QA/review               |
"""

import os
import re
import uuid
import datetime
import pandas as pd
from utils import load_content, segment_cultures, load_known_cultures
import logging
import sys

logging.basicConfig(filename='segmenter.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

try:
    from scripts.segment_by_culture import enrich_segments
except ImportError:
    enrich_segments = None

try:
    from langdetect import detect
    langdetect_available = True
except ImportError:
    langdetect_available = False

def safe_filename(title: str, segment_id: str = "") -> str:
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
    if segment_id:
        return f"{safe_title}_{segment_id[:6]}.md"
    return f"{safe_title}.md"

def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def enrich_metadata(seg, filepath, ts):
    seg['source_file'] = os.path.basename(filepath)
    seg['run_id'] = ts
    seg['segment_id'] = str(uuid.uuid4())
    return seg

def process_file(
    filepath: str,
    use_gpt: bool = True,
    section_summaries: bool = True,
    known_cultures_path: str = None,
) -> list:
    logging.info(f"Processing {filepath} with GPT={use_gpt}, section_summaries={section_summaries}")
    known_cultures = load_known_cultures(known_cultures_path) if known_cultures_path else set()
    text = load_content(filepath)
    segments = segment_cultures(text, known_cultures)
    ts = timestamp()
    for seg in segments:
        enrich_metadata(seg, filepath, ts)
    if use_gpt and enrich_segments:
        segments = enrich_segments(segments, section_summaries=section_summaries)
    # Language detection
    if langdetect_available:
        for seg in segments:
            try:
                seg["title_lang"] = detect(seg['title'])
            except Exception:
                seg["title_lang"] = "und"
    logging.info(f"Segmented {len(segments)} segments from {filepath}")
    return segments

def postprocess_segments(segments: list) -> list:
    for seg in segments:
        if 'segment_id' not in seg:
            seg['segment_id'] = str(uuid.uuid4())
        # Improved confidence heuristics
        summary = seg.get('summary', '')
        if 'summary_quality_score' in seg:
            seg['confidence_score'] = seg['summary_quality_score']
        elif len(summary) < 100 or summary.endswith('...'):
            seg['confidence_score'] = 'medium'
        else:
            seg['confidence_score'] = 'high'
        seg['needs_attention'] = (
            seg.get('confidence_score') in ['low', 'medium']
            or len(seg.get('content', '')) < 200
            or not seg.get('tags')
        )
    return segments

def export_segments_csv(segments: list, path: str):
    df = pd.DataFrame(segments)
    df.to_csv(path, index=False)

def markdown_with_frontmatter(seg):
    """Return Markdown with YAML frontmatter for a segment."""
    frontmatter = (
        f"---\n"
        f"title: \"{seg['title']}\"\n"
        f"tags: {seg.get('tags', '')}\n"
        f"lang: {seg.get('title_lang', 'und')}\n"
        f"confidence: {seg.get('confidence_score', '')}\n"
        f"run_id: {seg.get('run_id', '')}\n"
        f"---\n"
    )
    return f"{frontmatter}\n{seg['content']}\n"

def export_segments_markdown(segments: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(markdown_with_frontmatter(seg) + "\n")

def export_segments_per_markdown(segments: list, export_dir: str):
    os.makedirs(export_dir, exist_ok=True)
    for seg in segments:
        name = safe_filename(seg['title'], seg['segment_id'])
        with open(os.path.join(export_dir, name), "w", encoding="utf-8") as f:
            f.write(markdown_with_frontmatter(seg))

def update_repo_csv(segments: list, repo_path: str):
    logging.info(f"Updating repo CSV at {repo_path} with {len(segments)} segments")
    new_data = pd.DataFrame(segments)
    if os.path.exists(repo_path):
        repo_df = pd.read_csv(repo_path)
        repo_df = pd.concat([repo_df, new_data]).drop_duplicates()
    else:
        repo_df = new_data
    repo_df.to_csv(repo_path, index=False)
    logging.info(f"Repo CSV now contains {len(repo_df)} rows")
    return repo_df

def detect_duplicates(segments: list) -> set:
    titles = [s['title'] for s in segments]
    return set(t for t in titles if titles.count(t) > 1)

def filter_segments(segments: list, search: str) -> list:
    if not search:
        return segments
    return [s for s in segments if search.lower() in s['title'].lower() or search.lower() in s['content'].lower()]

def get_flagged_segments(segments: list) -> list:
    return [s for s in segments if s.get('needs_attention', False)]
