import streamlit as st
import pandas as pd
import json
import os

# Load i18n glossary
def load_i18n_glossary(path="i18n_glossary_template.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def translate_section(section, lang, glossary):
    return glossary.get(lang, {}).get(section, section)

# Load data (CSV or JSON)
def load_data(path):
    ext = os.path.splitext(path)[-1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    elif ext == ".json":
        return pd.read_json(path)
    else:
        st.error("Unsupported file type.")
        return pd.DataFrame()

st.set_page_config(page_title="Culture Profile Reviewer", layout="wide")
st.title("🌍 Culture Profile Reviewer")

# Sidebar: file selection and language
data_file = st.sidebar.file_uploader("Upload culture data (CSV or JSON)", type=["csv", "json"])
language = st.sidebar.selectbox("Language", ["en", "es", "fr"], index=0)
glossary = load_i18n_glossary()

if data_file:
    # Save uploaded file to temp
    temp_path = f".tmp_{data_file.name}"
    with open(temp_path, "wb") as f:
        f.write(data_file.read())
    df = load_data(temp_path)
    os.remove(temp_path)
    if not df.empty:
        cultures = df["culture"].unique()
        selected_culture = st.sidebar.selectbox("Select Culture", cultures)
        culture_df = df[df["culture"] == selected_culture]
        st.header(f"{selected_culture}")
        for _, row in culture_df.iterrows():
            st.subheader(translate_section(row["section"], language, glossary))
            st.markdown(f"**Summary:** {row.get('summary', '')}")
            st.markdown(f"**Section Summary:** {row.get('section_summary', '')}")
            st.markdown(f"**Content:**\n{row['content']}")
            st.markdown(f"**Confidence:** {row.get('confidence_score', '')}")
            st.markdown(f"**Needs Attention:** {row.get('needs_attention', False)}")
            st.markdown(f"**Review Prompt:** {row.get('gpt_review_prompt', '')}")
            st.markdown("---")
    else:
        st.warning("No data found in file.")
else:
    st.info("Upload a CSV or JSON file to begin reviewing.")
