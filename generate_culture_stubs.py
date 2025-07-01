import os
import json
import re
import argparse
import csv
import sys
from unidecode import unidecode
from tqdm import tqdm

# Simple mapping for common languages to standard-ish tags
LANGUAGE_TAG_MAP = {
    "english": "en", "spanish": "es", "french": "fr", "japanese": "ja",
    "chinese": "zh", "arabic": "ar", "portuguese": "pt", "german": "de",
    "russian": "ru", "korean": "ko", "italian": "it", "dutch": "nl",
    "swedish": "sv", "norwegian": "no", "danish": "da", "finnish": "fi",
    "greek": "el", "hebrew": "he", "hindi": "hi", "indonesian": "id",
    "malay": "ms", "thai": "th", "turkish": "tr", "vietnamese": "vi",
    "bengali": "bn", "punjabi": "pa", "urdu": "ur", "persian": "fa",
    "swahili": "sw", "amharic": "am", "hausa": "ha", "yoruba": "yo",
    "igbo": "ig", "somali": "so", "kurdish": "ku", "ukrainian": "uk",
    "polish": "pl", "romanian": "ro", "hungarian": "hu", "czech": "cs",
    "slovak": "sk", "bulgarian": "bg", "serbian": "sr", "croatian": "hr",
    "bosnian": "bs", "albanian": "sq", "georgian": "ka", "armenian": "hy",
    "azerbaijani": "az", "kazakh": "kk", "uzbek": "uz", "mongolian": "mn",
    "tibetan": "bo", "burmese": "my", "khmer": "km", "lao": "lo",
    "tagalog": "tl", "cebuano": "ceb", "malagasy": "mg", "nepali": "ne",
    "sinhala": "si", "tamil": "ta", "telugu": "te", "kannada": "kn",
    "malayalam": "ml", "gujarati": "gu", "marathi": "mr", "oriya": "or",
    "assamese": "as", "sindhi": "sd", "pashto": "ps", "balochi": "bal",
    "uyghur": "ug", "tibetan": "bo", "zulu": "zu", "xhosa": "xh",
    "afrikaans": "af", "sesotho": "st", "tswana": "tn", "shona": "sn",
    "kikuyu": "ki", "luganda": "lg", "kinyarwanda": "rw", "kirundi": "rn",
    "lingala": "ln", "wolof": "wo", "fulani": "ff", "manding": "man",
    "ewe": "ee", "akan": "ak", "ga": "gaa", "twi": "tw",
}

def get_language_tag(language_name, suppress_warnings=False):
    cleaned_name = language_name.lower().split('(')[0].strip()
    tag = LANGUAGE_TAG_MAP.get(cleaned_name)
    if not tag:
        if not suppress_warnings:
            print(f"⚠️  Warning: Language '{language_name}' not in tag map. Defaulting to 'und'.")
        return "und"
    return tag

def load_population_metadata(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {} # Return empty dict if file doesn't exist

def generate_culture_stubs(language_list_filepath, output_folder, population_metadata_path=None, suppress_warnings=False, skip_existing=False, sort_list=False, dry_run=False, log_csv_path=None, test_limit=None, verbose=False):
    os.makedirs(output_folder, exist_ok=True)

    if not os.path.exists(language_list_filepath):
        print(f"Error: Language list file not found at {language_list_filepath}")
        sys.exit(1)

    if not dry_run and os.listdir(output_folder):
        print(f"⚠️  Note: Output folder '{output_folder}' is not empty. Existing files may be overwritten unless --skip-existing is used.")

    with open(language_list_filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        if ',' in content:
            language_names = [name.strip() for name in content.split(',') if name.strip()]
        else:
            language_names = [line.strip() for line in content.splitlines() if line.strip()]

    if sort_list:
        language_names.sort()

    if test_limit:
        language_names = language_names[:test_limit]

    print(f"Found {len(language_names)} languages in the list.")

    unmatched_languages = []
    generated_count = 0
    csv_path = log_csv_path if log_csv_path else os.path.join(output_folder, "stub_index.csv")
    population_metadata = load_population_metadata(population_metadata_path) if population_metadata_path else {}

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Culture Name", "Language Tag", "Filename"])

        for lang_name in tqdm(language_names, desc="Generating stubs"):
            # Clean up language name for culture_name
            culture_name = re.sub(r'\s*\(.+\)', '', lang_name).strip() # Remove text in parentheses
            if not culture_name:
                continue # Skip empty names

            language_tag = get_language_tag(lang_name, suppress_warnings)
            if language_tag == "und":
                unmatched_languages.append(lang_name)

            filename = re.sub(r"[^\w\s-]", "", unidecode(culture_name)).replace(" ", "_").lower() + ".v3.json"
            filepath = os.path.join(output_folder, filename)

            if skip_existing and os.path.exists(filepath):
                continue

            if dry_run:
                print(f"[DRY-RUN] Would generate stub for '{culture_name}' with language tag '{language_tag}' at {filepath}")
                continue

            data = {
                "culture_name": culture_name,
                "language_tag": language_tag
            }

            # Inject population metadata if available
            if population_metadata.get(culture_name.lower()):
                data.update(population_metadata[culture_name.lower()])

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            generated_count += 1
            if verbose:
                print(f"Generated stub for '{culture_name}' with language tag '{language_tag}' at {filepath}")

            writer.writerow([culture_name, language_tag, filename])

    if unmatched_languages:
        unmatched_log = os.path.join(output_folder, "unmatched_languages.log")
        with open(unmatched_log, 'w', encoding='utf-8') as f:
            f.write("\n".join(unmatched_languages))
            f.write("\n\n# Total unmatched: {}\n".format(len(unmatched_languages)))
        print(f"⚠️  Unmatched languages logged to: {unmatched_log}")

    matched = len(language_names) - len(unmatched_languages)
    print(f"✅ Total entries processed: {len(language_names)}")
    print(f"✅ Match rate: {matched}/{len(language_names)} ({matched / len(language_names):.1%})")
    print(f"✅ New stubs generated: {generated_count}")
    print(f"📄 Stub index saved to: {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate JSON stubs for cultural enrichment.")
    parser.add_argument("--input", type=str, default="PGLS_List_of_Languages.txt", help="Path to language list (.txt)")
    parser.add_argument("--output", type=str, default="parsed_output", help="Folder to store .v3.json stubs")
    parser.add_argument("--population-metadata", type=str, help="Path to language population metadata JSON file")
    parser.add_argument("--suppress-warnings", action="store_true", help="Do not print unmatched language warnings.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip stub generation if file already exists.")
    parser.add_argument("--sort", action="store_true", help="Sort the language list alphabetically before processing.")
    parser.add_argument("--dry-run", action="store_true", help="Preview stubs that would be generated without writing them.")
    parser.add_argument("--log-csv-path", type=str, help="Optional path to write stub_index.csv.")
    parser.add_argument("--test", type=int, help="Only process the first N entries for testing.")
    parser.add_argument("--verbose", action="store_true", help="Enable per-stub output.")
    args = parser.parse_args()

    generate_culture_stubs(args.input, args.output, args.population_metadata, args.suppress_warnings, args.skip_existing, args.sort, args.dry_run, args.log_csv_path, args.test, args.verbose)
