import pandas as pd
import re
import logging
import csv
import json
import os
import argparse
import openai
import time
import concurrent.futures
from collections import defaultdict

# Logging: file + console
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('segmenter.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:%(message)s'))
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:%(message)s'))
logger.addHandler(console_handler)

openai.api_key = os.getenv("OPENAI_API_KEY")  # Set your OpenAI API key in the environment

def load_known_cultures(filepath):
    try:
        with open(filepath, encoding='utf-8') as f:
            return set(line.strip().upper() for line in f if line.strip())
    except FileNotFoundError:
        logging.warning("Known cultures file not found, using empty set.")
        return set()

KNOWN_CULTURES = load_known_cultures('known_cultures.txt')

def is_culture_title(line):
    clean = line.strip().upper()
    regex_match = bool(re.match(r'^[A-Z][A-Z\s\-]{2,}$', clean)) and len(clean) > 3
    known_match = clean in KNOWN_CULTURES
    return regex_match or known_match

def segment_cultures(text):
    lines = text.splitlines()
    segments = []
    current_title = None
    current_content = []
    overview = []
    found_first_culture = False

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if is_culture_title(line):
            title_lines = [line.strip()]
            while idx + 1 < len(lines) and is_culture_title(lines[idx + 1]):
                idx += 1
                title_lines.append(lines[idx].strip())
            title = ' '.join(title_lines)
            if not found_first_culture and current_content:
                overview = current_content
                current_content = []
                found_first_culture = True
            if current_title:
                segments.append({'title': current_title, 'content': '\n'.join(current_content)})
            current_title = title
            current_content = []
            found_first_culture = True
        else:
            current_content.append(line)
        idx += 1

    if current_title:
        segments.append({'title': current_title, 'content': '\n'.join(current_content)})
    elif current_content:
        if segments:
            logging.warning("Orphaned text found after last culture, appending to previous culture.")
            segments[-1]['content'] += '\n' + '\n'.join(current_content)
        else:
            overview = current_content

    if overview:
        segments.insert(0, {'title': 'Overview', 'content': '\n'.join(overview)})

    if not segments:
        logging.warning("No culture segments found in document.")
    for seg in segments:
        if not seg['content'].strip():
            logging.warning(f"Empty content for segment: {seg['title']}")

    return segments

def load_enrichment_rules(filepath='enrichment_rules.json'):
    try:
        with open(filepath, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

ENRICHMENT_RULES = load_enrichment_rules()

try:
    from tiktoken import get_encoding
    enc = get_encoding("cl100k_base")
except ImportError:
    enc = None
    logging.warning("tiktoken not installed; GPT input will be truncated by characters, not tokens.")

def truncate_for_gpt(text, max_tokens=1600):
    if enc:
        tokens = enc.encode(text)
        return enc.decode(tokens[:max_tokens])
    return text[:6000]  # fallback

def safe_gpt_call(prompt, model="gpt-4", retries=2, delay=3):
    for attempt in range(retries + 1):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.warning(f"GPT attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    return f"[GPT error after {retries+1} tries]"

def gpt_summarize(content, title):
    prompt = f"""
Summarize the cultural information below in 1–2 sentences. 
Focus on the worldview, social structure, traditions, and values of the {title} group.

{truncate_for_gpt(content)}
"""
    return safe_gpt_call(prompt)

def gpt_tags(content):
    prompt = f"""Extract 3–6 keywords or tags that reflect the core aspects of this culture: values, family structure, religion, traditions.

Return as a comma-separated list.

Text:
{truncate_for_gpt(content)}
"""
    return safe_gpt_call(prompt)

def confidence_score(enrichment, content):
    if "unknown" in [v.lower() for v in enrichment.values()]:
        return "low"
    elif len(content) < 300:
        return "medium"
    else:
        return "high"

def gpt_review_prompt(culture):
    return f"Does this summary fully capture the essence of {culture}? What might be missing?"

def load_language_services(filepath='language_services.json'):
    try:
        with open(filepath, encoding='utf-8') as f:
            return {entry['culture'].lower(): entry for entry in json.load(f)}
    except Exception:
        return {}

LANGUAGE_SERVICES = load_language_services()

def enrich_language_services(culture):
    return LANGUAGE_SERVICES.get(culture.lower(), {})

def segment_sections(content):
    lines = content.splitlines()
    sections = []
    current_section = "Uncategorized"
    current_content = []
    for line in lines:
        if (line.istitle() and 5 <= len(line.split()) <= 8) or (line.strip() in [
            "Orientation", "Economy", "Marriage and Family", "Religion and Expressive Culture",
            "Kinship", "Political Organization", "Socialization", "Health", "Death and Afterlife"
        ]):
            if current_content:
                sections.append({"section": current_section, "content": "\n".join(current_content)})
            current_section = line.strip()
            current_content = []
        else:
            current_content.append(line)
    if current_content:
        sections.append({"section": current_section, "content": "\n".join(current_content)})
    return sections

def load_content(input_path):
    ext = os.path.splitext(input_path)[-1].lower()
    if ext == ".txt":
        with open(input_path, encoding='utf-8') as f:
            return f.read()
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(input_path)
        return "\n".join(str(row['Content']).strip() for _, row in df.iterrows() if pd.notnull(row['Content']))
    elif ext == ".docx":
        import docx
        doc = docx.Document(input_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def export_json(segments, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

def export_csv(segments, out_path):
    fieldnames = [
        "culture", "section", "region", "language", "ethnicity", "summary", "tags",
        "confidence_score", "enrichment_notes", "language_services", "gpt_review_prompt", "content",
        "needs_attention", "section_summary"
    ]
    with open(out_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for seg in segments:
            writer.writerow(seg)

def export_markdown(segments, out_dir, summary_only=False):
    os.makedirs(out_dir, exist_ok=True)
    grouped = defaultdict(list)
    for seg in segments:
        grouped[seg['culture']].append(seg)
    # Create index.md for navigation
    with open(os.path.join(out_dir, "index.md"), "w", encoding="utf-8") as idx:
        idx.write("# Culture Index\n\n")
        for culture in sorted(grouped.keys()):
            slug = culture.replace(' ', '_').lower()
            idx.write(f"- [{culture}]({slug}.md)\n")
    for culture, entries in grouped.items():
        fname = f"{culture.replace(' ', '_').lower()}.md"
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
            f.write(f"# {culture}\n\n")
            f.write(f"**Region:** {entries[0].get('region','')}\n\n")
            f.write(f"**Language(s):** {entries[0].get('language','')}\n\n")
            f.write(f"**Ethnicity/Group:** {entries[0].get('ethnicity','')}\n\n")
            f.write(f"**Tags:** {entries[0].get('tags','')}\n\n")
            if summary_only:
                f.write(f"**Summary:** {entries[0].get('summary','')}\n\n")
            else:
                for seg in sorted(entries, key=lambda x: x['section']):
                    f.write(f"## {seg['section']}\n\n{seg['content']}\n\n")

def export_review_csv(segments, out_path):
    fieldnames = ["culture", "section", "summary", "confidence_score", "gpt_review_prompt", "needs_attention", "section_summary"]
    with open(out_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for seg in segments:
            writer.writerow({k: seg.get(k, "") for k in fieldnames})

def validate_profiles(csv_path):
    df = pd.read_csv(csv_path)
    required_sections = ["Orientation", "Economy", "Kinship"]
    for culture in df['culture'].unique():
        culture_df = df[df['culture'] == culture]
        for section in required_sections:
            if not any(culture_df['section'].str.contains(section, case=False, na=False)):
                print(f"❗ Missing section '{section}' in culture '{culture}'")
        if len(culture_df) < 2:
            print(f"⚠️ Only one section for culture '{culture}'")
        for _, row in culture_df.iterrows():
            if len(str(row['content'])) < 100:
                print(f"⚠️ Short content in {culture} - {row['section']}")

def enrich_culture(title, content):
    enrichment = {
        "Region": "Unknown",
        "Language(s)": "Unknown",
        "Ethnicity/Group": "Unknown",
        "Tags": "culture"
    }
    for rule in ENRICHMENT_RULES:
        if rule["match"].upper() in title.upper():
            enrichment.update({
                "Region": rule.get("region", enrichment["Region"]),
                "Language(s)": rule.get("language", enrichment["Language(s)"]),
                "Ethnicity/Group": rule.get("ethnicity", enrichment["Ethnicity/Group"]),
                "Tags": rule.get("tags", enrichment["Tags"])
            })
    return enrichment

def gpt_section_summary(content, section, culture):
    prompt = f"""
Summarize the section '{section}' for the culture '{culture}'.
Focus on key facts, values, or practices described in this section.

{truncate_for_gpt(content)}
"""
    return safe_gpt_call(prompt)

def main():
    parser = argparse.ArgumentParser(
        description="Segment, enrich, and validate global culture profiles with AI and rules.",
        epilog="Example: python segment_by_culture.py --input data.xlsx --use_gpt --out_dir outputs --out_csv export.csv --review_csv review.csv"
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--out_csv")
    parser.add_argument("--out_json")
    parser.add_argument("--out_md")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--use_gpt", action="store_true", help="Enable GPT enrichment")
    parser.add_argument("--parallel_gpt", action="store_true", help="Enable concurrent GPT enrichment")
    parser.add_argument("--review_csv", help="Export a simplified review sheet")
    parser.add_argument("--limit", type=int, help="Limit number of cultures for testing")
    parser.add_argument("--summary_only_md", help="Output summaries only per culture in Markdown")
    parser.add_argument("--out_dir", help="Base output directory for all exports")
    args = parser.parse_args()

    text = load_content(args.input)
    raw_segments = segment_cultures(text)
    if args.limit:
        raw_segments = raw_segments[:args.limit]
    segments = []
    gpt_jobs = []
    def enrich_row(seg, section):
        enrich = enrich_culture(seg['title'], section['content'])
        if args.use_gpt:
            gpt_summary = gpt_summarize(section['content'], seg['title'])
            gpt_taglist = gpt_tags(section['content'])
            section_summary = gpt_section_summary(section['content'], section['section'], seg['title'])
        else:
            gpt_summary = section['content'][:150].replace('\n', ' ') + "..."
            gpt_taglist = "culture"
            section_summary = ""
        lang_services = enrich_language_services(seg['title'])
        score = confidence_score(enrich, section['content'])
        notes = ""
        if enrich["Region"] == "Unknown" or "[GPT error" in gpt_summary:
            notes = "Review required – missing metadata or summary failure."
        unknown_fields = sum(1 for k in ["Region", "Language(s)", "Ethnicity/Group"] if enrich[k] == "Unknown")
        needs_attention = (len(section['content']) < 100) or (unknown_fields >= 3)
        return {
            "culture": seg['title'],
            "section": section['section'],
            "region": enrich["Region"],
            "language": enrich["Language(s)"],
            "ethnicity": enrich["Ethnicity/Group"],
            "summary": gpt_summary,
            "tags": gpt_taglist,
            "confidence_score": score,
            "enrichment_notes": notes,
            "language_services": json.dumps(lang_services, ensure_ascii=False),
            "gpt_review_prompt": gpt_review_prompt(seg['title']),
            "content": section['content'],
            "needs_attention": needs_attention,
            "section_summary": section_summary
        }
    if args.use_gpt and args.parallel_gpt:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for seg in raw_segments:
                for section in segment_sections(seg['content']):
                    futures.append(executor.submit(enrich_row, seg, section))
            for f in concurrent.futures.as_completed(futures):
                segments.append(f.result())
    else:
        for seg in raw_segments:
            for section in segment_sections(seg['content']):
                segments.append(enrich_row(seg, section))

    # Output directory logic
    out_dir = args.out_dir or ""
    def outpath(sub, fname):
        return os.path.join(out_dir, sub, fname) if out_dir else fname
    if args.out_csv:
        os.makedirs(os.path.join(out_dir, "csv"), exist_ok=True) if out_dir else None
        export_csv(segments, outpath("csv", os.path.basename(args.out_csv)))
    if args.out_json:
        os.makedirs(os.path.join(out_dir, "json"), exist_ok=True) if out_dir else None
        export_json(segments, outpath("json", os.path.basename(args.out_json)))
    if args.out_md:
        os.makedirs(os.path.join(out_dir, "markdown"), exist_ok=True) if out_dir else None
        export_markdown(segments, outpath("markdown", ""), summary_only=False)
    if args.summary_only_md:
        os.makedirs(os.path.join(out_dir, "markdown"), exist_ok=True) if out_dir else None
        export_markdown(segments, outpath("markdown", ""), summary_only=True)
    if args.review_csv:
        os.makedirs(os.path.join(out_dir, "review"), exist_ok=True) if out_dir else None
        export_review_csv(segments, outpath("review", os.path.basename(args.review_csv)))
    if args.validate:
        validate_profiles(args.out_csv or args.out_json)

# Minimal test harness for dev/debugging
if __name__ == "__main__" and os.getenv("DEBUG"):
    sample_text = "JAPANESE\nOrientation\nJapan is an island nation..."
    segs = segment_cultures(sample_text)
    print(json.dumps(segs, indent=2))

if __name__ == "__main__":
    main()
