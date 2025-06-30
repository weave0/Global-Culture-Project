"""
cli.py - Command-line interface for the Global Culture Project pipeline.
Calls core.py functions for batch processing, enrichment, and export.
"""
import argparse
import sys
from core import process_file, postprocess_segments, export_segments_csv, export_segments_markdown, export_segments_per_markdown, update_repo_csv

def main():
    parser = argparse.ArgumentParser(description="Global Culture Project CLI")
    parser.add_argument('input', nargs='+', help='Input file(s) (.docx, .xlsx, .txt)')
    parser.add_argument('--gpt', action='store_true', help='Use GPT enrichment')
    parser.add_argument('--section-summaries', action='store_true', help='Add section-level summaries')
    parser.add_argument('--csv', help='Export all segments to this CSV file')
    parser.add_argument('--md', help='Export all segments to this Markdown file')
    parser.add_argument('--md-dir', help='Export each segment as Markdown to this directory')
    parser.add_argument('--repo', help='Update the global repo CSV with new segments')
    parser.add_argument('--known-cultures', help='Path to known_cultures.txt')
    args = parser.parse_args()

    all_segments = []
    for filepath in args.input:
        segments = process_file(
            filepath,
            use_gpt=args.gpt,
            section_summaries=args.section_summaries,
            known_cultures_path=args.known_cultures,
        )
        segments = postprocess_segments(segments)
        all_segments.extend(segments)

    if args.csv:
        export_segments_csv(all_segments, args.csv)
        print(f"Exported {len(all_segments)} segments to {args.csv}")
    if args.md:
        export_segments_markdown(all_segments, args.md)
        print(f"Exported Markdown to {args.md}")
    if args.md_dir:
        export_segments_per_markdown(all_segments, args.md_dir)
        print(f"Exported Markdown files to {args.md_dir}")
    if args.repo:
        update_repo_csv(all_segments, args.repo)
        print(f"Updated repo CSV at {args.repo}")

if __name__ == "__main__":
    main()
