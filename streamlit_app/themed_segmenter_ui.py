# themed_segmenter_ui.py — Oceanic Cosmos Streamlit UI for Global Culture Project
#
# Copilot Guidance Prompts:
# - TODO: Add Markdown export per-segment (named by title + ID) to outputs_ui/
# - TODO: Integrate AgGrid review table if st_aggrid is installed
# - TODO: Append results to Global_Culture_Repository_Output.csv, avoiding dupes
# - TODO: Provide option to flag segments needing manual review
# - TODO: Add theme toggle in sidebar (dark/ocean vs light/sunrise)
# - TODO: Log run details to segmenter.log
# - TODO: Expose CLI-equivalent trigger via run_pipeline.py

import streamlit as st
import os
import time
import pandas as pd
import datetime
import sys
import os
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from core import process_file, postprocess_segments, export_segments_csv, export_segments_per_markdown, update_repo_csv

# === VISUAL & AMBIENT === #
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500&display=swap" rel="stylesheet">
<style>
body {
    background: linear-gradient(180deg, #011627 0%, #001F3F 100%);
    color: #e0f7fa;
    font-family: 'Unbounded', sans-serif;
}
h1, h2, h3 {
    text-shadow: 0 0 5px rgba(255,255,255,0.2);
}
[data-testid="stAppViewContainer"] {
    background-color: transparent;
}
.star {
    position: fixed;
    width: 6px;
    height: 6px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    animation: float 6s ease-in-out infinite;
    pointer-events: none;
}
@keyframes float {
    0%   { transform: translateY(0);   opacity: 0.4; }
    50%  { transform: translateY(-15px); opacity: 0.8; }
    100% { transform: translateY(0);   opacity: 0.4; }
}
.star:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; }
.star:nth-child(2) { top: 50%; left: 40%; animation-delay: 1s; }
.star:nth-child(3) { top: 70%; left: 70%; animation-delay: 2s; }
</style>
<div class="star"></div><div class="star"></div><div class="star"></div>
""", unsafe_allow_html=True)

# Optional ambient sound (user-toggle)
if st.checkbox("🔊 Ocean Ambience"):
    st.audio("https://cdn.pixabay.com/download/audio/2022/03/15/audio_b0a56b4a03.mp3", format="audio/mp3", start_time=0)

# === MAIN UI === #
# Copilot Guidance Prompts:
# - TODO: Add Markdown export per-segment (named by title + ID) to outputs_ui/
# - TODO: Integrate AgGrid review table if st_aggrid is installed
# - TODO: Append results to Global_Culture_Repository_Output.csv, avoiding dupes
# - TODO: Provide option to flag segments needing manual review
# - TODO: Add theme toggle in sidebar (dark/ocean vs light/sunrise)
# - TODO: Log run details to segmenter.log
# - TODO: Expose CLI-equivalent trigger via run_pipeline.py

# --- AgGrid Integration ---
aggrid_available = False
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    aggrid_available = True
except ImportError:
    st.info("Install st-aggrid for advanced review/editing table features.")

# --- Theme Toggle in Sidebar ---
theme = st.sidebar.radio("Theme", ["Ocean (Dark)", "Sunrise (Light)"])
test_mode = st.sidebar.checkbox("Test Mode (no file writes)", value=False)
if theme == "Sunrise (Light)":
    st.markdown("""
    <style>
    body { background: linear-gradient(180deg, #f8fafc 0%, #ffe082 100%); color: #222; }
    h1, h2, h3 { text-shadow: none; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("# 🌊 Global Culture Segmenter")
st.markdown("Let the current carry your data into clarity.")

uploaded_file = st.file_uploader("📄 Upload a document", type=["docx", "xlsx", "txt"])
use_gpt = st.checkbox("✨ Use GPT enrichment (summary, tags, section summary)", value=True)
confirm = st.checkbox("✅ I confirm I want to run the segmenter")

if uploaded_file and confirm:
    if st.button("🚀 Begin Cultural Segmentation"):
        try:
            # Save and load
            os.makedirs("input_docs", exist_ok=True)
            path = os.path.join("input_docs", uploaded_file.name)
            with open(path, "wb") as f:
                f.write(uploaded_file.read())

            segments = process_file(path, use_gpt=use_gpt)
            segments = postprocess_segments(segments)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            run_id = f"{uploaded_file.name}-{ts}"

            df = pd.DataFrame(segments)
            st.success(f"Processed {len(df)} segments")

            # Show previews
            for seg in segments[:3]:
                with st.expander(f"🔹 {seg['title']}"):
                    st.markdown(seg.get('summary', ''))
                    st.text_area("Excerpt", seg['content'][:500] + "...", height=150)

            # Save to outputs
            outdir = f"outputs_ui/{ts}"
            os.makedirs(outdir, exist_ok=True)
            if not test_mode:
                df.to_csv(f"{outdir}/output.csv", index=False)

            st.download_button("⬇️ Download CSV", data=df.to_csv(index=False).encode("utf-8"),
                               file_name="culture_segments.csv", mime="text/csv")

            # Markdown export per-segment
            if st.button("Export Segments as Markdown"):
                if not test_mode:
                    export_segments_per_markdown(segments, outdir)
                st.success(f"Exported Markdown files to {outdir}")

            # Append to repo (with deduplication)
            if st.button("Append to Master Repo CSV"):
                repo_path = "Global_Culture_Repository_Output.csv"
                if not test_mode:
                    # Deduplicate by unique segment ID or title+content
                    try:
                        if os.path.exists(repo_path):
                            repo_df = pd.read_csv(repo_path)
                            combined = pd.concat([repo_df, df], ignore_index=True)
                            if 'id' in combined.columns:
                                combined = combined.drop_duplicates(subset=['id'])
                            else:
                                combined = combined.drop_duplicates(subset=['title', 'content'])
                            combined.to_csv(repo_path, index=False)
                            st.success(f"Appended {len(df)} segments (deduped) to {repo_path}")
                        else:
                            df.to_csv(repo_path, index=False)
                            st.success(f"Created {repo_path} with {len(df)} segments")
                    except Exception as repo_err:
                        st.error(f"Repo append error: {repo_err}")
                else:
                    st.info("Test mode: Repo append skipped.")

            # AgGrid review/edit table
            if aggrid_available:
                st.markdown("### 🧱 Review/Edit Segments (AgGrid)")
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_default_column(editable=True, wrapText=True, autoHeight=True)
                gb.configure_column('content', width=400, wrapText=True, editable=True)
                gb.configure_column('tags', editable=True)
                gb.configure_column('confidence_score', editable=True)
                gb.configure_column('needs_attention', editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': [True, False]})
                grid_options = gb.build()
                grid_response = AgGrid(
                    df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=True,
                    allow_unsafe_jscode=True,
                    height=400,
                )
                edited_df = grid_response['data']
                st.info("Review and edit as needed before export or repo append.")
                # Use edited_df for downstream export/append if needed

            # --- Flag segments needing manual review ---
            if 'needs_attention' in df.columns:
                flagged_count = df['needs_attention'].sum() if df['needs_attention'].dtype==bool else (df['needs_attention']==True).sum()
                if flagged_count > 0:
                    st.warning(f"{flagged_count} segments flagged for manual review.")
                    def highlight_flagged(val):
                        return 'background-color: #ffcccc' if val else ''
                    st.dataframe(df.style.applymap(highlight_flagged, subset=['needs_attention']))

            # --- Log run details to segmenter.log ---
            try:
                if not test_mode:
                    with open('segmenter.log', 'a', encoding='utf-8') as logf:
                        logf.write(f"{datetime.datetime.now().isoformat()} | File: {uploaded_file.name} | Segments: {len(df)} | GPT: {use_gpt}\n")
            except Exception as logerr:
                st.warning(f"Could not write to segmenter.log: {logerr}")

        except Exception as e:
            st.error(f"💥 Error: {e}")
else:
    st.info("Awaiting file and confirmation.")
