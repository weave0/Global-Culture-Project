# 📁 File: generate_enrichment_report.py
# Description: Generates an HTML report from JSON suggestions for human review

import os
import json
import hashlib
import argparse
from jinja2 import Environment, FileSystemLoader
from collections import Counter
from jsonschema import validate, ValidationError
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import requests

INPUT_SUGGESTIONS = "sharepoint_output/suggestions.json"
OUTPUT_REPORT = "sharepoint_output/enrichment_report.html"
SUMMARY_JSON = "sharepoint_output/report_meta.json"
TEMPLATE_DIR = "templates"
TEMPLATE_NAME = "enrichment_report.html"
CACHE_FILE = "sharepoint_output/.suggestions_hash"

SUGGESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "culture_name": {"type": "string"},
        "field": {"type": "string"},
        "original_value": {},
        "suggested_value": {}
    },
    "required": ["culture_name", "field", "original_value", "suggested_value"]
}

# Load environment variables from .env file
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SHAREPOINT_SITE = os.getenv("SHAREPOINT_SITE")
SHAREPOINT_TOKEN = os.getenv("SHAREPOINT_TOKEN")


def calculate_hash(file_path):
    """Calculate the hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def validate_suggestions(suggestions):
    """Validate the structure of suggestions using JSON schema."""
    for suggestion in suggestions:
        validate(instance=suggestion, schema=SUGGESTION_SCHEMA)


def write_summary_metadata(suggestions, output_path):
    """Write summary metadata to a JSON file."""
    cultures = {s["culture_name"] for s in suggestions}
    field_counts = Counter(s["field"] for s in suggestions)
    most_common = field_counts.most_common(1)[0] if field_counts else ("—", 0)

    metadata = {
        "cultures_enriched": len(cultures),
        "most_enriched_field": most_common[0],
        "fields_touched": list(field_counts.keys())
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def notify_user(email, report_path):
    """Send an email notification with the report link."""
    body = f"The enrichment report has been generated: {report_path}"
    msg = MIMEText(body)
    msg['Subject'] = "Your Enrichment Report is Ready"
    msg['From'] = SMTP_USER
    msg['To'] = email

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"📧 Notification sent to {email}")
    except Exception as e:
        print(f"Error sending email: {e}")


def upload_to_sharepoint(file_path):
    """Upload the report to SharePoint using Microsoft Graph API."""
    headers = {
        "Authorization": f"Bearer {SHAREPOINT_TOKEN}",
        "Content-Type": "application/json"
    }
    upload_url = f"{SHAREPOINT_SITE}/_api/web/GetFolderByServerRelativeUrl('Shared Documents')/Files/add(url='{os.path.basename(file_path)}',overwrite=true)"

    try:
        with open(file_path, "rb") as f:
            response = requests.post(upload_url, headers=headers, data=f)
        if response.status_code == 200:
            print(f"✅ Report uploaded to SharePoint: {file_path}")
        else:
            print(f"Error uploading to SharePoint: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error during SharePoint upload: {e}")


def generate_enrichment_report(input_path, output_path, verbose, force):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    # Check if the input JSON has changed
    current_hash = calculate_hash(input_path)
    if not force and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cached_hash = f.read().strip()
        if current_hash == cached_hash:
            print("✅ No changes detected in suggestions. Skipping report generation.")
            return

    with open(input_path, "r", encoding="utf-8") as f:
        suggestions = json.load(f)

    # Validate suggestions
    try:
        validate_suggestions(suggestions)
    except ValidationError as e:
        print(f"Error: {e.message}")
        return

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_NAME)

    rendered = template.render(suggestions=suggestions)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    # Update the hash cache
    with open(CACHE_FILE, "w") as f:
        f.write(current_hash)

    # Write summary metadata
    write_summary_metadata(suggestions, SUMMARY_JSON)

    if verbose:
        print(f"✅ Suggestions loaded: {len(suggestions)}")
        print(f"📄 Writing HTML to: {output_path}")
        print(f"📊 Summary metadata written to: {SUMMARY_JSON}")

    print(f"✅ Enrichment report created at {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an enrichment report from JSON suggestions.")
    parser.add_argument("--input", type=str, default=INPUT_SUGGESTIONS, help="Path to the input JSON file.")
    parser.add_argument("--output", type=str, default=OUTPUT_REPORT, help="Path to the output HTML file.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed execution information.")
    parser.add_argument("--force", action="store_true", help="Force report generation even if unchanged.")
    parser.add_argument("--upload", action="store_true", help="Upload the generated report to SharePoint.")
    parser.add_argument("--email", type=str, help="Email address to notify after report generation.")
    args = parser.parse_args()

    generate_enrichment_report(args.input, args.output, args.verbose, args.force)

    if args.upload:
        upload_to_sharepoint(args.output)

    if args.email:
        notify_user(args.email, args.output)