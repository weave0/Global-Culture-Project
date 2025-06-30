import pandas as pd
import re

# Load your previously extracted file
input_file = r"d:\Global Culture Project\All_Text_Extraction.xlsx"
output_file = r"d:\Global Culture Project\Segmented_Culture_Content.xlsx"

df = pd.read_excel(input_file)

# Known section headings from culture docs
section_titles = [
    "Orientation", "History and Cultural Relations", "Settlements",
    "Economy", "Kinship", "Marriage and Family", "Sociopolitical Organization",
    "Religion and Expressive Culture", "Bibliography", "See also"
]

def is_all_caps(text):
    return text.isupper() and len(text.split()) <= 4

def segment_rows(rows):
    segmented = []
    current_culture = None
    current_section = None

    for _, row in rows.iterrows():
        text = str(row.get("Content", "")).strip()
        if not text:
            continue

        # New culture heading
        if is_all_caps(text) or re.match(r"^Culture of ", text, re.IGNORECASE):
            current_culture = text
            current_section = None
        elif text in section_titles:
            current_section = text
        else:
            segmented.append({
                "Culture Name": current_culture,
                "Section": current_section,
                "Content": text,
                "Source File": row.get("File Name"),
                "File Type": row.get("File Type"),
                "File Path": row.get("File Path"),
                "Extracted At": row.get("Extracted At"),
                "Inferred Tags": "",
                "Summary": "",
                "Notes": ""
            })

    return pd.DataFrame(segmented)

# Segment and save
segmented_df = segment_rows(df)
segmented_df.to_excel(output_file, index=False)
print(f"✅ Segmentation complete. Output saved to:\n{output_file}")
