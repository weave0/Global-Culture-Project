import os
import glob
import datetime
import pandas as pd
from utils import load_content, segment_cultures, load_known_cultures

def discover_input_files(input_dir="input_docs"):
    os.makedirs(input_dir, exist_ok=True)
    return glob.glob(f"{input_dir}/*.docx") + glob.glob(f"{input_dir}/*.xlsx") + glob.glob(f"{input_dir}/*.txt")

def assign_metadata(segments, source_file, run_id=None):
    if run_id is None:
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for seg in segments:
        seg['source_file'] = os.path.basename(source_file)
        seg['run_id'] = run_id
    return segments

def filter_segments(segments, search):
    if not search:
        return segments
    return [s for s in segments if search.lower() in s.get('title','').lower() or search.lower() in s.get('content','').lower()]

def append_to_repo(new_data, repo_path="Global_Culture_Repository_Output.csv"):
    if os.path.exists(repo_path):
        repo_df = pd.read_csv(repo_path)
        repo_df = pd.concat([repo_df, new_data]).drop_duplicates()
    else:
        repo_df = new_data
    repo_df.to_csv(repo_path, index=False)
    return len(repo_df)
