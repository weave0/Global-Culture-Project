import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import openai
import logging
import time
import sys
import csv
import coloredlogs

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load prompts from an external JSON file
PROMPTS_FILE = Path("prompts.json")
if PROMPTS_FILE.exists():
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        PROMPTS = json.load(f)
else:
    raise FileNotFoundError(f"Prompts file not found: {PROMPTS_FILE}")

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
coloredlogs.install(level=logging.INFO, logger=logger, fmt="%(asctime)s - %(levelname)s - %(message)s")

# Validate prompt placeholders
for field, prompt in PROMPTS.items():
    if "{culture_name}" not in prompt:
        logger.warning(f"Prompt for '{field}' may be missing '{{culture_name}}' placeholder.")

def load_culture_data(filepath):
    if Path(filepath).exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}  # Return empty dict if file doesn't exist

def save_culture_data(filepath, data):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def enrich_culture_with_ai(culture_name, existing_data, force_enrich=False, omit_errors=False, system_prompt="You are an expert in global cultural anthropology."):
    logger.info(f"Enriching {culture_name} with AI...")
    enriched_data = existing_data.copy()

    # Ensure 'culture_name' field is set
    if 'culture_name' not in enriched_data or not enriched_data['culture_name']:
        enriched_data['culture_name'] = culture_name

    # Ensure 'language_tag' field is set, default to 'und' if not present
    if 'language_tag' not in enriched_data or not enriched_data['language_tag']:
        enriched_data['language_tag'] = "und"

    for field, prompt_template in tqdm(PROMPTS.items(), desc=f"Enriching fields for {culture_name}"):
        if force_enrich or (field not in enriched_data or not enriched_data[field]):
            prompt = prompt_template.format(culture_name=culture_name)
            retries = 3
            for attempt in range(retries):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=600
                    )
                    enriched_data[field] = response.choices[0].message.content.strip()
                    enriched_data['model_used'] = response.model
                    logger.debug(f"  - Enriched '{field}'")
                    break
                except openai.error.OpenAIError as e:
                    logger.warning(f"  - Error enriching '{field}' on attempt {attempt + 1}: {e}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    if attempt == retries - 1:
                        if omit_errors:
                            logger.warning(f"  - Omitted '{field}' due to persistent errors.")
                            continue
                        enriched_data[field] = f"[ERROR: {str(e)}]"
        else:
            logger.debug(f"  - Skipping '{field}' (already has content)")

    if 'source' not in enriched_data:
        enriched_data['source'] = "AI Enrichment (OpenAI GPT)"

    enriched_data['enriched_timestamp'] = datetime.utcnow().isoformat() + "Z"

    return enriched_data

def log_enriched_fields(log_file, filename, enriched_fields):
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for field in enriched_fields:
            writer.writerow([filename, field])

def main():
    parser = argparse.ArgumentParser(description="AI-powered culture data enrichment script.")
    parser.add_argument("--input", type=str, help="Path to the input folder containing .v3.json files.")
    parser.add_argument("--output", type=str, help="Path to the output folder where enriched .v3.json files will be saved.")
    parser.add_argument("--file", type=str, help="Optional single .v3.json file to enrich.")
    parser.add_argument("--overwrite-existing-fields", action="store_true", help="Force enrichment of all fields, even if they already have content.")
    parser.add_argument("--preview-only", action="store_true", help="Preview changes without saving output.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("--quiet", action="store_true", help="Suppress all logging except errors.")
    parser.add_argument("--system-prompt", type=str, default="You are an expert in global cultural anthropology.",
                        help="System prompt used to guide GPT behavior.")
    parser.add_argument("--omit-errors", action="store_true", help="Do not include failed enrichment fields in output.")
    parser.add_argument("--max-files", type=int, help="Limit the number of files processed (for testing).")
    parser.add_argument("--no-backup", action="store_true", help="Skip saving backups of original files.")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.ERROR)

    input_folder = args.input
    output_folder = args.output
    single_file = args.file
    force_enrich = args.overwrite_existing_fields
    dry_run = args.preview_only
    system_prompt = args.system_prompt
    omit_errors = args.omit_errors
    max_files = args.max_files
    no_backup = args.no_backup

    log_file = Path(output_folder) / "enriched_fields_log.csv"
    if not log_file.exists():
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Filename", "Enriched Field"])

    if single_file:
        culture_files = [Path(single_file).name]
        input_folder = str(Path(single_file).parent)
    else:
        if not Path(input_folder).exists():
            logger.error(f"Input folder does not exist: {input_folder}")
            return
        culture_files = [f.name for f in Path(input_folder).glob("*.v3.json")]

    if not culture_files:
        logger.error(f"No .v3.json files found in input folder: {input_folder}")
        logger.info("Tip: You can generate base .v3.json files with: python generate_culture_stubs.py --input ...")
        return

    if max_files:
        culture_files = culture_files[:max_files]

    logger.info(f"Found {len(culture_files)} culture files in input folder: {input_folder}")
    logger.info(f"Run Parameters: overwrite-existing-fields={force_enrich}, preview-only={dry_run}, omit-errors={omit_errors}, no-backup={no_backup}")
    logger.info(f"System Prompt: {system_prompt[:60]}{'...' if len(system_prompt) > 60 else ''}")

    processed, skipped, failed = 0, 0, 0

    for i, filename in enumerate(tqdm(culture_files, desc="Processing files"), start=1):
        input_filepath = Path(input_folder) / filename
        existing_data = load_culture_data(input_filepath)

        if not existing_data:
            logger.warning(f"{filename} appears empty or malformed, skipping.")
            skipped += 1
            continue

        culture_name = existing_data.get('culture_name', filename.replace(".v3.json", ""))
        language_tag = existing_data.get('language_tag', 'und')

        try:
            enriched_data = enrich_culture_with_ai(culture_name, existing_data, force_enrich, omit_errors, system_prompt)

            enriched_fields = [field for field in enriched_data if enriched_data[field] != existing_data.get(field)]

            if dry_run:
                if enriched_fields:
                    logger.info(f"[PREVIEW-ONLY] Changes for {filename}:")
                    for field in enriched_fields:
                        logger.info(f"  - {field}: {existing_data.get(field)} -> {enriched_data[field]}")
                else:
                    logger.info(f"[PREVIEW-ONLY] No changes for {filename}.")
                skipped += 1
                continue

            if not no_backup:
                backup_folder = Path(output_folder) / "backups" / language_tag
                backup_folder.mkdir(parents=True, exist_ok=True)
                backup_path = backup_folder / filename
                if not backup_path.exists():
                    save_culture_data(backup_path, existing_data)

            lang_output_folder = Path(output_folder) / language_tag
            output_filepath = lang_output_folder / filename

            save_culture_data(output_filepath, enriched_data)
            log_enriched_fields(log_file, filename, enriched_fields)

            logger.info(f"[{i}/{len(culture_files)}] Enriched and saved: {output_filepath}")
            processed += 1
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            failed += 1

    enriched_field_count = sum(1 for _ in open(log_file)) - 1
    logger.info(f"Summary: Processed={processed}, Skipped={skipped}, Failed={failed}, Fields Enriched={enriched_field_count}")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
