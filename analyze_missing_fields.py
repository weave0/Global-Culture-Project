# 📁 File: analyze_missing_fields.py
# Description: Analyzes manifest.json to identify and aggregate missing fields across all cultures

import os
import json
from collections import defaultdict

INPUT_MANIFEST = "sharepoint_output/manifest.json"
OUTPUT_ANALYSIS = "sharepoint_output/missing_fields_analysis.json"

def analyze_missing_fields():
    if not os.path.exists(INPUT_MANIFEST):
        print(f"Error: {INPUT_MANIFEST} not found.")
        return

    with open(INPUT_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    missing_fields_agg = defaultdict(int)
    culture_missing_fields = {}

    for entry in manifest:
        culture_name = entry.get("culture_name", "Unknown")
        missing_fields = entry.get("missing_fields", [])
        culture_missing_fields[culture_name] = missing_fields

        for field in missing_fields:
            missing_fields_agg[field] += 1

    analysis = {
        "missing_fields_aggregation": dict(missing_fields_agg),
        "culture_missing_fields": culture_missing_fields
    }

    os.makedirs(os.path.dirname(OUTPUT_ANALYSIS), exist_ok=True)
    with open(OUTPUT_ANALYSIS, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"✅ Missing fields analysis created at {OUTPUT_ANALYSIS}")

if __name__ == "__main__":
    analyze_missing_fields()