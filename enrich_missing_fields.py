import json
import os

REQUIRED_FIELDS = ["culture_name", "region", "language_tags", "communication_style", "social_norms"]

def load_manifest(path="manifest.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def enrich_entry(entry):
    missing = [f for f in REQUIRED_FIELDS if not entry.get(f)]
    prompts = {}
    for field in missing:
        if field == "communication_style":
            prompts[field] = f"Describe typical communication style for {entry.get('culture_name', 'this culture')}."
        elif field == "social_norms":
            prompts[field] = f"What are key social norms in {entry.get('region', 'this region')}?"
        else:
            prompts[field] = f"Please provide {field}."
    return prompts

def main():
    manifest = load_manifest()
    for entry in manifest:
        prompts = enrich_entry(entry)
        if prompts:
            out = {
                "culture_name": entry.get("culture_name"),
                "missing_fields": prompts
            }
            fname = f"enrich_{entry.get('culture_name', 'unknown').replace(' ', '_').lower()}.json"
            with open(os.path.join("reports", fname), "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
            print(f"Enrichment scaffold written: reports/{fname}")

if __name__ == "__main__":
    main()