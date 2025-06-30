"""
cli_minimal.py - Minimal CLI for quick single-file segmentation and export.

Usage:
    python cli_minimal.py input_docs/sample.txt --csv output.csv --repo Global_Culture_Repository_Output.csv
"""
import argparse
from core import process_file, postprocess_segments, export_segments_csv, update_repo_csv

def main():
    parser = argparse.ArgumentParser(description="Run cultural segmentation pipeline")
    parser.add_argument("file", help="Input file (.docx, .xlsx, .txt)")
    parser.add_argument("--csv", help="Output CSV path", default="output.csv")
    parser.add_argument("--repo", help="Repo CSV path", default="Global_Culture_Repository_Output.csv")
    args = parser.parse_args()

    segments = process_file(args.file)
    segments = postprocess_segments(segments)
    export_segments_csv(segments, args.csv)
    update_repo_csv(segments, args.repo)

if __name__ == "__main__":
    main()
