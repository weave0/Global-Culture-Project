import os
import json
import argparse
import csv

PROMPTS = {
    "summary": "Provide a concise summary of the culture of {culture_name}.",
    "greetings": "Describe common greetings in {culture_name}.",
    "taboos": "What are common taboos in {culture_name}?",
    "gestures": "Explain common gestures in {culture_name}.",
    "religion": "Describe the main religious practices and beliefs in {culture_name}.",
    "gender_roles": "Discuss traditional and modern gender roles in {culture_name}.",
    "communication_style": "Describe the typical communication style in {culture_name} (e.g., direct/indirect, high/low context).",
    "clothing": "Describe traditional and common modern clothing styles in {culture_name}.",
    "estimated_speakers": "Roughly how many people speak {culture_name} worldwide?",
    "primary_regions": "List the countries where {culture_name} is most commonly spoken."
}

def load_culture_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {} # Return empty dict if file doesn't exist

def save_culture_data(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_field_content(field, prompt, culture_name):
    # Placeholder for AI API call
    return f"AI generated content for {field} in {culture_name} based on prompt: '{prompt}'"

def enrich_culture_with_ai(culture_name, existing_data, population_data, force_enrich=False):
    """
    Placeholder for AI enrichment logic.
    This function would call an AI model (e.g., OpenAI GPT)
    to generate content for the fields.
    """
    print(f"Simulating AI enrichment for {culture_name}...")
    enriched_data = existing_data.copy()

    # Ensure 'culture_name' field is set
    if 'culture_name' not in enriched_data or not enriched_data['culture_name']:
        enriched_data['culture_name'] = culture_name

    # Ensure 'language_tag' field is set, default to 'und' if not present
    if 'language_tag' not in enriched_data or not enriched_data['language_tag']:
        enriched_data['language_tag'] = "und"

    # Normalize and warn if the language_tag is missing or incorrect
    language_tag = enriched_data.get("language_tag", "und").lower()
    if language_tag == "und":
        print(f"⚠️ Warning: No language tag for {culture_name}. Defaulting to 'und'")

    # Add population data if available
    culture_key = culture_name.lower()
    if culture_key in population_data:
        enriched_data.update(population_data[culture_key])

    # Example of how you would iterate and call AI for each field
    for field, prompt_template in PROMPTS.items():
        # Only enrich if field is empty or if force_enrich is True
        if force_enrich or (field not in enriched_data or not enriched_data[field]):
            prompt = prompt_template.format(culture_name=culture_name)
            # In a real scenario, you'd call your AI model here:
            # import openai
            # openai.api_key = os.getenv("OPENAI_API_KEY") # Make sure to set your API key as an environment variable
            # response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=500)
            # enriched_data[field] = response.choices[0].text.strip()
            enriched_data[field] = generate_field_content(field, prompt, culture_name)
            print(f"  - Enriched '{field}'")
        else:
            print(f"  - Skipping '{field}' (already has content)")

    # Add a source field if not present
    if 'source' not in enriched_data:
        enriched_data['source'] = "AI Enrichment (Simulated)"

    return enriched_data

def main():
    parser = argparse.ArgumentParser(description="AI-powered culture data enrichment script.")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to the input folder containing .v3.json files.")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to the output folder where enriched .v3.json files will be saved.")
    parser.add_argument("--force", action="store_true",
                        help="Force enrichment of all fields, even if they already have content.")
    # Optional: Support partial enrichment of fields
    parser.add_argument("--fields", nargs="*", help="Only enrich these fields.")
    parser.add_argument("--flat", action="store_true", help="Save enriched files to output root (no language folders).")
    args = parser.parse_args()

    input_folder = args.input
    output_folder = args.output
    force_enrich = args.force

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Load population data
    population_data = load_culture_data("d:/Global Culture Project/language_population_data.json")

    # Get list of culture files from input folder
    culture_files = [f for f in os.listdir(input_folder) if f.endswith(".v3.json")]

    if not culture_files:
        print(f"No .v3.json files found in input folder: {input_folder}")
        print("Please run generate_culture_stubs.py first to create initial files.")
        return
    else:
        print(f"Found {len(culture_files)} culture files in input folder: {input_folder}")
        if os.path.abspath(input_folder) == os.path.abspath(output_folder):
            print("⚠️ Warning: Input and output folders are the same. Files will be overwritten.")

        summary_rows = []

        # Validate --fields input
        if args.fields:
            invalid = [f for f in args.fields if f not in PROMPTS]
            if invalid:
                print(f"⚠️ Invalid field(s) in --fields: {', '.join(invalid)}. Skipping.")
            selected_prompts = {k: PROMPTS[k] for k in args.fields if k in PROMPTS}
        else:
            selected_prompts = PROMPTS

        for filename in culture_files:
            input_filepath = os.path.join(input_folder, filename)
            existing_data = load_culture_data(input_filepath)

            culture_name = existing_data.get('culture_name', filename.replace(".v3.json", ""))
            enriched_data = enrich_culture_with_ai(culture_name, existing_data, population_data, force_enrich)
            language_tag = enriched_data.get('language_tag', 'und').lower()

            # Save enriched file
            output_filepath = (
                os.path.join(output_folder, filename) if args.flat else os.path.join(output_folder, language_tag, filename)
            )
            save_culture_data(output_filepath, enriched_data)

            # Capture summary info
            completed = sum(1 for k in PROMPTS if enriched_data.get(k, "").strip())
            total = len(PROMPTS)
            summary_rows.append([culture_name, language_tag, completed, total])

            print(f"✅ Enriched and saved: {output_filepath}")

        # Sort summary rows by completion
        summary_rows.sort(key=lambda x: x[2])

        # Generate summary report
        report_path = os.path.join(output_folder, "enrichment_report.csv")
        with open(report_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["culture_name", "language_tag", "fields_completed", "fields_total"])
            writer.writerows(summary_rows)

        print(f"📊 Enrichment report saved to: {report_path}")
        print(f"\n🎉 Finished enriching {len(summary_rows)} cultures.")
        print(f"📄 Enrichment report available at: {report_path}")
        print("You can now open this report to prioritize final review.")

if __name__ == "__main__":
    main()
