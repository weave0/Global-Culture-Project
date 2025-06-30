"""
review_tool.py - Minimal standalone viewer/editor for segment CSVs.

This tool can be run as a Streamlit app or CLI for quick review and editing of segment CSVs.

TODO:
- Make columns editable inline (e.g., tags, confidence_score) using st_aggrid
- Highlight rows where 'needs_attention' == True
- Add checkbox toggle: Show flagged segments only
- Let user export flagged rows separately (review.csv)
- Add filter/search bar for titles/tags/content
- Add option to save output to outputs_ui/ with timestamp
"""

import streamlit as st
import pandas as pd
import os

def main():
    st.title("Segment Review Tool")
    uploaded = st.file_uploader("Upload a segment CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df)
        st.download_button("Download Edited CSV", df.to_csv(index=False).encode("utf-8"), file_name="edited_segments.csv")

if __name__ == "__main__":
    main()
