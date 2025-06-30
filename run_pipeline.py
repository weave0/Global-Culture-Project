"""
run_pipeline.py - CLI runner for batch/automation workflows.
Supports batch file processing, session config/log export, and diagnostics.
"""
# TODO: Add --validate flag to run schema or field completeness checks
# TODO: Add --ignore-dupes flag for repo appends to enforce stricter deduplication
# TODO: Enable --format md|csv|json to control output structure
# TODO: Support parallel processing via ThreadPool for large file sets
# TODO: Integrate langdetect + enrich_segments fallback if missing
# TODO: Allow --tag or --filter flags to limit output by content
# TODO: Allow --run-id override for session tracking

from core import process_file, postprocess_segments, export_segments_csv
from core import export_segments_per_markdown, update_repo_csv, get_flagged_segments
from segment_quality import quality_report
import argparse
import datetime
import json
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs='+', help="Path(s) to input file(s) (.docx, .txt, .xlsx)")
    parser.add_argument("--gpt", action="store_true", help="Use GPT enrichment")
    parser.add_argument("--out", default="output.csv", help="CSV output path (merged)")
    parser.add_argument("--session-log", default=None, help="Path to save session config/log as JSON")
    parser.add_argument("--diagnostics", default=None, help="Path to save diagnostics summary as JSON")
    parser.add_argument("--markdown", default=None, help="Directory to export per-segment Markdown files")
    parser.add_argument("--repo", default=None, help="Append to Global_Culture_Repository_Output.csv")
    parser.add_argument("--review-only", default=None, help="Export flagged segments to review.csv")
    parser.add_argument("--log", default=None, help="Write a JSON or YAML run summary (auto-detect by extension)")
    parser.add_argument("--batch", default=None, help="Directory to process all files in (overrides positional files)")
    args = parser.parse_args()

    # Directory-wide batch mode
    if args.batch:
        batch_dir = args.batch
        files = [os.path.join(batch_dir, f) for f in os.listdir(batch_dir)
                 if f.lower().endswith(('.docx', '.txt', '.xlsx'))]
        args.files = files
        print(f"Batch mode: found {len(files)} files in {batch_dir}")

    all_segments = []
    session_info = {
        'run_time': datetime.datetime.now().isoformat(),
        'files': args.files,
        'gpt': args.gpt,
        'outputs': [],
        'diagnostics': {},
    }
    for file in args.files:
        segs = process_file(file, use_gpt=args.gpt)
        segs = postprocess_segments(segs)
        all_segments.extend(segs)
        session_info['outputs'].append({'file': file, 'segments': len(segs)})

    export_segments_csv(all_segments, args.out)
    print(f"✅ Done. Exported {len(all_segments)} segments to {args.out}")

    # Markdown export
    if args.markdown:
        export_segments_per_markdown(all_segments, args.markdown)
        print(f"Exported Markdown files to {args.markdown}")

    # Repo append
    if args.repo:
        update_repo_csv(all_segments, args.repo)
        print(f"Appended {len(all_segments)} segments to {args.repo}")

    # Review-only export
    if args.review_only:
        flagged = get_flagged_segments(all_segments)
        import pandas as pd
        pd.DataFrame(flagged).to_csv(args.review_only, index=False)
        print(f"Exported {len(flagged)} flagged segments to {args.review_only}")

    # Save session config/log
    if args.session_log:
        with open(args.session_log, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, indent=2)
        print(f"Session log saved to {args.session_log}")

    # Diagnostics summary
    diag = quality_report(all_segments)
    session_info['diagnostics'] = diag
    if args.diagnostics:
        with open(args.diagnostics, 'w', encoding='utf-8') as f:
            json.dump(diag, f, indent=2)
        print(f"Diagnostics summary saved to {args.diagnostics}")
    else:
        print("Diagnostics summary:")
        for k, v in diag.items():
            print(f"  {k}: {v}")

    # Log run summary (JSON or YAML)
    if args.log:
        if args.log.lower().endswith('.yaml') or args.log.lower().endswith('.yml'):
            try:
                import yaml
                with open(args.log, 'w', encoding='utf-8') as f:
                    yaml.dump(session_info, f)
                print(f"Run summary written to {args.log} (YAML)")
            except ImportError:
                print("PyYAML not installed. Please install with 'pip install pyyaml' to use YAML logging.")
        else:
            with open(args.log, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, indent=2)
            print(f"Run summary written to {args.log} (JSON)")

# TODO: Add --log flag to write a JSON/YAML run summary
# TODO: Support directory-wide processing with --batch input_docs/

if __name__ == "__main__":
    main()
