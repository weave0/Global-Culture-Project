import os
import json
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

def main():
    # Paths
    json_path = "missing_report.json"
    template_dir = "templates"
    template_name = "missing_fields_report_template.html"
    output_dir = "reports"
    output_path = os.path.join(output_dir, "missing_fields_report.html")

    # Load JSON data
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            analysis = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: '{json_path}' not found.")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Failed to parse '{json_path}': {e}")
        return

    # Set up Jinja2 environment
    try:
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
    except TemplateNotFound:
        print(f"❌ Error: Template '{template_name}' not found in '{template_dir}'.")
        return

    # Render HTML
    try:
        html = template.render(analysis=analysis)
    except Exception as e:
        print(f"❌ Error during template rendering: {e}")
        return

    # Write output
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Report generated: {output_path}")
    except Exception as e:
        print(f"❌ Error writing report: {e}")

if __name__ ==