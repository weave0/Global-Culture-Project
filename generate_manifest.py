# 📁 File: generate_manifest.py
# Description: Scans parsed_output/ and generates manifest.json summarizing all cultures

import os
import json
import csv
from datetime import datetime

# Expected fields checklist for all entries
expected_fields = [
    "overview", "geographic_context", "historical_background",
    "family_structure", "gender_roles", "intergenerational_values",
    "religion_and_spirituality", "dietary_practices", "health_beliefs_and_practices",
    "communication_style", "language_tags", "social_norms_and_etiquette",
    "notable_celebrations_or_rituals", "arts_and_expressive_culture", "economic_life",
    "migration_and_diaspora", "legal_system_and_rights", "technology_and_digital_life",
    "climate_and_environmental_life", "intra_cultural_variation",
    "interpreter_or_service_notes"
]

INPUT_DIR = "parsed_output"
OUTPUT_MANIFEST = "sharepoint_output/manifest.json"

manifest = []

for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".v3.json"):
        path = os.path.join(INPUT_DIR, filename)
        try:
            with open(path, encoding="utf-8") as f:
                entry = json.load(f)

            culture_name = entry.get("culture_name", os.path.splitext(filename)[0]).strip()
            region = entry.get("region", "Unknown").strip()
            languages = entry.get("language_tags", [])
            if isinstance(languages, str):
                languages = [languages]

            # Calculate completion percentage
            filled_fields = [f for f in expected_fields if entry.get(f)]
            completion = round(len(filled_fields) / len(expected_fields) * 100, 1)

            # Flatten missing fields for diagnostics
            missing_fields = [field for field in expected_fields if not entry.get(field)]

            last_updated = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")

            manifest.append({
                "filename": filename,
                "culture_name": culture_name,
                "region": region,
                "language_tags": languages,
                "missing_fields": missing_fields,
                "completion_percent": completion,
                "last_updated": last_updated,
                "html_path": filename.replace(".v3.json", ".html"),
            })

        except Exception as e:
            print(f"⚠️ Error reading {filename}: {e}")

# Sort manifest by completion percentage and culture name
manifest.sort(key=lambda x: (-x["completion_percent"], x["culture_name"].lower()))

# Write the manifest
os.makedirs(os.path.dirname(OUTPUT_MANIFEST), exist_ok=True)
with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

# Write CSV manifest
csv_path = OUTPUT_MANIFEST.replace(".json", ".csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "culture_name", "region", "language_tags", "completion_percent", "missing_fields"])
    for item in manifest:
        writer.writerow([
            item["filename"],
            item["culture_name"],
            item["region"],
            ", ".join(item["language_tags"]),
            item["completion_percent"],
            ", ".join(item["missing_fields"])
        ])

print(f"✅ Manifest created with {len(manifest)} entries at {OUTPUT_MANIFEST}")
print(f"📄 CSV manifest also written to: {csv_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="parsed_output", help="Folder with .v3.json files")
    parser.add_argument("--output", default="sharepoint_output/manifest.json", help="Output path for manifest.json")
    args = parser.parse_args()

    INPUT_DIR = args.input
    OUTPUT_MANIFEST = args.output