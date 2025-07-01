from jinja2 import Environment, FileSystemLoader
import os
import json
import argparse
import subprocess

try:
    import yaml
except ImportError:
    yaml = None

import datetime

def render_card(entry: dict, output_path: str, *, template_name='card_template.html', flag=None, generated_on=None, source_docx=None, dry_run=False, sections=None, labels=None):
    if dry_run:
        print(f"[DRY RUN] Would render: {output_path}")
        return None

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(template_name)
    culture_name = entry.get("culture_name", "")
    rendered = template.render(
        entry=entry,
        culture_name=culture_name,
        flag=flag,
        generated_on=generated_on,
        source_docx=source_docx,
        sections=sections,
        labels=labels
    )
    with open(output_path, "w", encoding="utf-8") as outf:
        outf.write(rendered)
    return rendered

def iso_to_flag(code):
    return ''.join(chr(127397 + ord(c)) for c in code.upper()) if code and len(code) == 2 else ""

def load_settings(settings_path="settings.yaml"):
    if yaml and os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render SharePoint cards from JSON entries.")
    parser.add_argument("--input", type=str, default="parsed_output", help="Input directory containing .v3.json files")
    parser.add_argument("--output", type=str, default="sharepoint_output", help="Output directory for rendered HTML files")
    parser.add_argument("--upload", action="store_true", help="Upload rendered files to SharePoint")
    parser.add_argument("--dry-run", action="store_true", help="Preview which files would be rendered")
    parser.add_argument("--settings", type=str, default="settings.yaml", help="YAML config file for paths/templates")
    args = parser.parse_args()

    # Load settings if available
    settings = load_settings(args.settings)
    template_name = settings.get("template", "card_template.html")

    # Create output directory if missing (unless dry-run)
    if not args.dry_run:
        os.makedirs(args.output, exist_ok=True)

    # Define sections and labels (can be loaded from settings.yaml if desired)
    sections = settings.get("sections") or {
        "Cultural Background": ["overview", "geographic_context", "historical_background"],
        "Social Structure": ["family_structure", "gender_roles", "intergenerational_values"],
        "Beliefs & Practices": ["religion_and_spirituality", "dietary_practices", "health_beliefs_and_practices"],
        "Communication": ["communication_style", "language_tags"],
        "Society & Life": ["social_norms_and_etiquette", "notable_celebrations_or_rituals", "arts_and_expressive_culture",
            "economic_life", "migration_and_diaspora", "legal_system_and_rights", "technology_and_digital_life",
            "climate_and_environmental_life", "intra_cultural_variation"],
        "Service Notes": ["interpreter_or_service_notes"]
    }
    labels = settings.get("labels") or {
        "arts_and_expressive_culture": "Arts & Culture",
        "dietary_practices": "Food & Diet",
        "interpreter_or_service_notes": "Interpreter Notes"
    }

    # Load or initialize render log
    render_log_path = os.path.join(args.output, "render_log.json")
    if os.path.exists(render_log_path):
        with open(render_log_path, "r", encoding="utf-8") as logf:
            render_log = json.load(logf)
    else:
        render_log = {}

    rendered_count = 0
    for filename in os.listdir(args.input):
        if filename.endswith(".v3.json"):
            input_path = os.path.join(args.input, filename)
            output_path = os.path.join(args.output, filename.replace(".v3.json", ".html"))

            # Only re-render entries modified since last render (unless dry-run)
            if not args.dry_run and os.path.exists(output_path) and os.path.getmtime(input_path) <= os.path.getmtime(output_path):
                continue

            try:
                with open(input_path, encoding="utf-8") as f:
                    entry = json.load(f)

                flag = iso_to_flag(entry.get("region"))
                generated_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                source_docx = entry.get("source_docx")

                # Jinja2 fallback warning for missing fields
                missing_fields = [field for group in sections.values() for field in group if not entry.get(field)]
                if "language_tags" in missing_fields:
                    print(f"⚠️  {filename}: 'language_tags' missing.")

                render_card(
                    entry, output_path,
                    template_name=template_name,
                    flag=flag,
                    generated_on=generated_on,
                    source_docx=source_docx,
                    dry_run=args.dry_run,
                    sections=sections,
                    labels=labels
                )
                rendered_count += 1
                render_log[filename] = {
                    "output": output_path,
                    "status": "success",
                    "timestamp": generated_on,
                    "missing_fields": missing_fields
                }
                if not args.dry_run:
                    print(f"✅ Rendered: {output_path}")
                else:
                    print(f"[DRY RUN] Would render: {output_path}")
            except Exception as e:
                render_log[filename] = {
                    "output": output_path,
                    "status": "error",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error": str(e)
                }
                print(f"❌ Failed to render {filename}: {e}")

    # Write render log
    if not args.dry_run:
        with open(render_log_path, "w", encoding="utf-8") as logf:
            json.dump(render_log, logf, indent=2)

    # Export a separate index.html that links to all output files
    if not args.dry_run:
        index_path = os.path.join(args.output, "index.html")
        with open(index_path, "w", encoding="utf-8") as index_file:
            index_file.write("<html><body><h1>Rendered SharePoint Cards</h1><ul>")
            for filename in os.listdir(args.output):
                if filename.endswith(".html"):
                    index_file.write(f'<li><a href="{filename}">{filename}</a></li>')
            index_file.write("</ul></body></html>")
        print(f"✅ Index file created at {index_path}")
        print(f"✅ Total cards rendered: {rendered_count}")

    # Upload to SharePoint if --upload flag is passed
    if args.upload and not args.dry_run:
        try:
            result = subprocess.run(["powershell", "./upload_to_sharepoint.ps1"], capture_output=True, text=True)
            print("📤 Upload output:\n", result.stdout)
            if result.stderr:
                print("⚠️ Upload errors:\n", result.stderr)
        except Exception as e:
            print(f"❌ Failed to trigger SharePoint upload: {e}")