"""
confidence.py - Abstract scoring logic for segment confidence.

This module is intended to provide advanced, pluggable confidence scoring for cultural segments.
Future: Integrate ML/AI or rule-based scoring, fallback to heuristics in core.py.
"""

def score_confidence(segment):
    # Placeholder: use summary_quality_score if present, else fallback
    if 'summary_quality_score' in segment:
        return segment['summary_quality_score']
    summary = segment.get('summary', '')
    if len(summary) < 100 or summary.endswith('...'):
        return 'medium'
    return 'high'
