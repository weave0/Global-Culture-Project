# 📁 File: render_missing_fields_report.py
# Description: Renders a visual overview of missing fields analysis using Jinja2

import os
import json
from jinja2 import Environment, FileSystemLoader

INPUT_ANALYSIS = "sharepoint_output/missing_fields_analysis.json"
OUTPUT_REPORT = "sharepoint_output/missing_fields_report.html"
TEMPLATE_DIR = "templates"
TEMPLATE_NAME = "missing_fields_report.html"


def render_missing_fields_report():
    if not os.path.exists(INPUT_ANALYSIS):
        print(f"Error: {INPUT_ANALYSIS} not found.")
        return

    with open(INPUT_ANALYSIS, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_NAME)

    rendered = template.render(analysis=analysis)

    os.makedirs(os.path.dirname(OUTPUT_REPORT), exist_ok=True)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"✅ Missing fields report created at {OUTPUT_REPORT}")


if __name__ == "__main__":
    render_missing_fields_report()