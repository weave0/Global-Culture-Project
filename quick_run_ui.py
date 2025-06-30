import streamlit as st
import os
import time
import pandas as pd
import glob
import datetime
import uuid
import re
from utils import load_content, segment_cultures, load_known_cultures
# Assume enrich_segments is your GPT enrichment function
try:
    from scripts.segment_by_culture import enrich_segments
except ImportError:
    enrich_segments = None  # fallback if not available

# AgGrid import
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    aggrid_available = True
except ImportError:
    aggrid_available = False

# Language detection import
try:
    from langdetect import detect
    langdetect_available = True
except ImportError:
    langdetect_available = False

st.set_page_config(page_title="Culture Segmenter Runner", page_icon="🌍", layout="centered")

# Auto-switch theme based on time
hour = datetime.datetime.now().hour
st.write(f"🕒 Local time: {hour}:00")
if hour < 6 or hour > 18:
    st.markdown("<style>body { background-color: #111; color: #eee; }</style>", unsafe_allow_html=True)

st.markdown("""
# 🌍 Global Culture Segmenter UI
Welcome! Ingest, segment, and enrich your cultural data below.
""")

# 1. Auto-discover files in input_docs/
os.makedirs("input_docs", exist_ok=True)
input_options = glob.glob("input_docs/*.docx") + glob.glob("input_docs/*.xlsx") + glob.glob("input_docs/*.txt")

# Batch file selection
selected_files = st.multiselect("Choose one or more files to segment", input_options)
uploaded_files = st.file_uploader("Or upload documents (batch supported)", type=["docx", "xlsx", "txt"], accept_multiple_files=True)

# If files are uploaded, save them to input_docs/ and add to selected_files
if uploaded_files:
    for uploaded_file in uploaded_files:
        save_path = os.path.join("input_docs", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.read())
        st.success(f"Uploaded and saved as {save_path}")
        if save_path not in selected_files:
            selected_files.append(save_path)

use_gpt = st.checkbox("Use GPT enrichment (summary, tags, section summary)", value=True)
section_summaries = st.checkbox("Add section-level summaries", value=True)
confirm = st.checkbox("✅ I confirm I want to run the segmenter")

# Search/filter tool
search = st.text_input("🔍 Search segments by culture or keyword (after run)")

# Add a toggle to show segments needing attention
show_attention = st.checkbox("Show segments needing attention (empty content, missing tags, low confidence)")

# Session log display
if os.path.exists("segmenter.log"):
    with st.expander("View recent session log"):
        with open("segmenter.log", "r", encoding="utf-8") as logf:
            st.text(logf.read()[-5000:])

# Track last upload for reprocessing
if 'last_upload' not in st.session_state:
    st.session_state['last_upload'] = None
if uploaded_files:
    st.session_state['last_upload'] = [os.path.join("input_docs", f.name) for f in uploaded_files]

# Track last run_id for deletion
if 'last_run_id' not in st.session_state:
    st.session_state['last_run_id'] = None

if st.session_state['last_upload']:
    if st.button("Reprocess Last Upload"):
        selected_files = st.session_state['last_upload']
        st.info(f"Reprocessing {selected_files}")
    if st.button("Delete Last Entry from Repo"):
        repo_path = "Global_Culture_Repository_Output.csv"
        if os.path.exists(repo_path) and st.session_state['last_run_id']:
            repo_df = pd.read_csv(repo_path)
            if 'run_id' in repo_df.columns:
                repo_df = repo_df[repo_df['run_id'] != st.session_state['last_run_id']]
                repo_df.to_csv(repo_path, index=False)
                st.success("Deleted last entry from repo.")

# Only show the button if both input and confirmation are valid
review_only = st.checkbox("🔍 Review-only mode (no repo update, export flagged for review)", value=False)
test_mode = st.radio("Mode", ["Test Mode (no file writes)", "Production Mode (writes to repo)"])
if test_mode == "Test Mode (no file writes)":
    st.warning("Test Mode: No changes will be written to disk or repo.")
else:
    st.success("Production Mode: Changes will be written to the master repo.")

if selected_files and confirm:
    if st.button("🚀 Run Segmenter (Batch)"):
        all_segments = []
        overall_progress = st.progress(0, text="Batch progress...")
        for file_idx, selected_file in enumerate(selected_files):
            if not os.path.exists(selected_file):
                st.error(f"❌ File not found: {selected_file}")
                continue
            st.info(f"Processing {selected_file} ({file_idx+1}/{len(selected_files)})")
            progress = st.progress(0, text="Starting segmentation...")
            try:
                known_path = "known_cultures.txt" if os.path.exists("known_cultures.txt") else None
                known_cultures = load_known_cultures(known_path) if known_path else set()
                text = load_content(selected_file)
                segments = segment_cultures(text, known_cultures)
                total = len(segments)
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                for seg in segments:
                    seg['source_file'] = os.path.basename(selected_file)
                    seg['run_id'] = ts
                if use_gpt and enrich_segments:
                    segments = enrich_segments(segments, section_summaries=section_summaries)
                # Language detection integration (if not already present)
                if langdetect_available:
                    for seg in segments:
                        try:
                            seg["title_lang"] = detect(seg['title'])
                        except:
                            seg["title_lang"] = "und"
                for i, seg in enumerate(segments):
                    time.sleep(0.05)
                    progress.progress((i + 1) / total, text=f"Processing: {i+1} of {total}")
                all_segments.extend(segments)
                overall_progress.progress((file_idx + 1) / len(selected_files), text=f"Batch: {file_idx+1}/{len(selected_files)} done")
            except Exception as e:
                st.error(f"💥 Failed to process {selected_file}: {e}")
                st.exception(e)
        if all_segments:
            # Assign unique IDs and needs_attention flag
            for seg in all_segments:
                seg["segment_id"] = str(uuid.uuid4())
                # GPT confidence override
                if seg.get('summary', '').endswith('...'):
                    seg['confidence_score'] = 'medium'
                seg['needs_attention'] = (
                    seg.get('confidence_score') in ['low', 'medium']
                    or len(seg.get('content', '')) < 200
                    or not seg.get('tags')
                )
            st.metric("Segments Processed", len(all_segments))
            st.metric("Flagged for Review", sum(s.get('needs_attention', False) for s in all_segments))
            # Show segments needing attention
            if show_attention:
                df = pd.DataFrame(all_segments)
                flagged = df[df['needs_attention']]
                st.dataframe(flagged[['title', 'confidence_score', 'tags', 'content']].fillna(''))
            # Detect duplicate segment titles
            titles = [s['title'] for s in all_segments]
            dupes = set(t for t in titles if titles.count(t) > 1)
            if dupes:
                st.warning(f"Duplicate segment titles detected: {', '.join(dupes)}")
            # Filter segments if search is used
            filtered = all_segments
            if search:
                filtered = [s for s in all_segments if search.lower() in s['title'].lower() or search.lower() in s['content'].lower()]
            # Inline Markdown Preview (expanders)
            for seg in filtered[:10]:
                with st.expander(f"📘 {seg['title']}"):
                    st.markdown(f"**Confidence:** {seg.get('confidence_score', '')}  ")
                    st.markdown(f"**Tags:** {seg.get('tags', '')}  ")
                    st.markdown(f"**Language:** {seg.get('title_lang', '')}")
                    st.markdown(seg['content'])
            # --- AgGrid Editor ---
            if aggrid_available:
                st.markdown("### 🧱 Edit Segments Before Saving (AgGrid)")
                df_edit = pd.DataFrame(all_segments)
                gb = GridOptionsBuilder.from_dataframe(df_edit)
                gb.configure_default_column(editable=True, wrapText=True, autoHeight=True)
                gb.configure_column('content', width=400, wrapText=True, editable=True)
                gb.configure_column('tags', editable=True)
                gb.configure_column('confidence', editable=True)
                gb.configure_column('title_lang', editable=False)
                gb.configure_column('needs_attention', editable=False, cellStyle={'color': 'red'})
                gb.configure_column('segment_id', editable=False)
                grid_options = gb.build()
                grid_response = AgGrid(
                    df_edit,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=True,
                    allow_unsafe_jscode=True,
                    height=400,
                )
                edited_df = grid_response['data']
                st.info("Review and edit as needed. Click below to save to the master repo.")
                # Export filtered/edited subset
                if filtered:
                    csv_filtered = pd.DataFrame(filtered).to_csv(index=False).encode('utf-8')
                    st.download_button("Download Filtered Segments", csv_filtered, file_name="filtered.csv", mime="text/csv")
                if review_only:
                    flagged = edited_df[edited_df.get('flagged', False) == True] if 'flagged' in edited_df else edited_df
                    st.download_button("Download Review CSV (flagged only)", flagged.to_csv(index=False).encode('utf-8'), file_name="review.csv", mime="text/csv")
                    st.warning("Review-only mode: Not updating master repo until approved.")
                    if st.button("✅ Approve & Commit to Repo"):
                        if test_mode == "Production Mode (writes to repo)":
                            repo_path = "Global_Culture_Repository_Output.csv"
                            if os.path.exists(repo_path):
                                repo_df = pd.read_csv(repo_path)
                                repo_df = pd.concat([repo_df, flagged]).drop_duplicates()
                            else:
                                repo_df = flagged
                            repo_df.to_csv(repo_path, index=False)
                            st.success(f"Committed {len(flagged)} flagged segments to {repo_path} (now {len(repo_df)} rows)")
                        else:
                            st.info("Test Mode: No changes written.")
                else:
                    if st.button("✅ Approve & Commit to Repo"):
                        if test_mode == "Production Mode (writes to repo)":
                            repo_path = "Global_Culture_Repository_Output.csv"
                            if os.path.exists(repo_path):
                                repo_df = pd.read_csv(repo_path)
                                repo_df = pd.concat([repo_df, edited_df]).drop_duplicates()
                            else:
                                repo_df = edited_df
                            repo_df.to_csv(repo_path, index=False)
                            st.success(f"Committed {len(edited_df)} segments to {repo_path} (now {len(repo_df)} rows)")
                        else:
                            st.info("Test Mode: No changes written.")
            else:
                st.warning("Install streamlit-aggrid for interactive editing: pip install streamlit-aggrid")
            if not langdetect_available:
                st.warning("Install langdetect for language detection: pip install langdetect")
            # Auto-organize exports by timestamp
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = f"outputs_ui/{ts}"
            os.makedirs(export_dir, exist_ok=True)
            if test_mode == "Production Mode (writes to repo)":
                repo_path = "Global_Culture_Repository_Output.csv"
                new_data = pd.DataFrame(all_segments)
                if os.path.exists(repo_path):
                    repo_df = pd.read_csv(repo_path)
                    repo_df = pd.concat([repo_df, new_data]).drop_duplicates()
                else:
                    repo_df = new_data
                repo_df.to_csv(repo_path, index=False)
                st.success(f"Appended to {repo_path} (now {len(repo_df)} rows)")
            else:
                st.info("Test Mode: No changes written to repo.")
            # Download just this run's segments (CSV)
            csv_data = new_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download This Batch CSV", csv_data, file_name="output.csv", mime="text/csv")
            # Markdown export
            st.download_button("Download Markdown", md_data, file_name="output.md", mime="text/markdown")
            # Output each segment to Markdown (safe filenames)
            for seg in all_segments:
                safe_title = re.sub(r'[\\/*?:"<>|]', "_", seg['title'])
                name = f"{safe_title}_{seg['segment_id'][:6]}.md"
                with open(os.path.join(export_dir, name), "w", encoding="utf-8") as f:
                    f.write(f"# {seg['title']}\n\n{seg['content']}")
            # Mini unit log
            with st.expander("⚙️ Segment Diagnostics"):
                bads = [s for s in all_segments if len(s.get('content', '')) < 100]
                if bads:
                    st.warning(f"{len(bads)} segments are extremely short.")
                else:
                    st.info("No extremely short segments detected.")
            # Enrichment profile summary
            st.info(f"🔍 {sum(s.get('confidence_score')=='high' for s in all_segments)} high-confidence segments")
            if test_mode == "Production Mode (writes to repo)" and 'repo_df' in locals():
                st.info(f"📊 Repo now contains {len(repo_df)} rows across {repo_df['title'].nunique()} cultures.")
else:
    st.info("Awaiting your confirmation and at least one file to start.")
