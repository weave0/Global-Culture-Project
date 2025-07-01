import os
import json
import csv

REQUIRED_FIELDS = ["culture_name", "region", "language_tags"]

def load_manifest(path="manifest.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_manifest(manifest, path="manifest.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def validate_entry(entry):
    missing = [field for field in REQUIRED_FIELDS if not entry.get(field)]
    return missing

def suggest_missing_fields(entry):
    suggestions = {}
    if not entry.get("language_tags"):
        suggestions["language_tags"] = "What languages are spoken in this culture's region?"
    if not entry.get("region"):
        suggestions["region"] = "What is the primary country or region for this culture?"
    # Add more heuristics as needed
    return suggestions

def manual_entry():
    entry = {}
    for field in REQUIRED_FIELDS:
        entry[field] = input(f"Enter {field}: ").strip()
    missing = validate_entry(entry)
    if missing:
        print(f"⚠ Missing required fields: {', '.join(missing)}")
        suggestions = suggest_missing_fields(entry)
        for field, prompt in suggestions.items():
            print(f"Suggestion for {field}: {prompt}")
    return entry

def csv_entries(csv_path):
    entries = []
    with open(csv_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            entry = {field: row.get(field, "").strip() for field in REQUIRED_FIELDS}
            entries.append(entry)
    return entries

def generate_starter_json(entry, output_dir="parsed_output"):
    os.makedirs(output_dir, exist_ok=True)
    fname = f"{entry['culture_name'].replace(' ', '_').lower()}.v3.json"
    path = os.path.join(output_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)
    print(f"Starter file created: {path}")

def main():
    print("Culture Ingestion Tool")
    manifest = load_manifest()
    mode = input("Add manually (m) or from CSV (c)? [m/c]: ").strip().lower()
    new_entries = []
    if mode == "c":
        csv_path = input("Enter CSV file path: ").strip()
        new_entries = csv_entries(csv_path)
    else:
        entry = manual_entry()
        new_entries = [entry]

    for entry in new_entries:
        missing = validate_entry(entry)
        if missing:
            print(f"⚠ Entry for '{entry.get('culture_name', '[unknown]')}' missing: {', '.join(missing)}")
            suggestions = suggest_missing_fields(entry)
            for field, prompt in suggestions.items():
                print(f"Suggestion for {field}: {prompt}")
        manifest.append(entry)
        if input("Generate starter .v3.json file? [y/N]: ").strip().lower() == "y":
            generate_starter_json(entry)

    save_manifest(manifest)
    print("✅ Manifest updated.")

if __name__ == "__main__":
    main()