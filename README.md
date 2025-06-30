# 🌍 Global Culture Project

> **NOTICE:**  
> This project is for educational and non-commercial purposes only.  
> *“Brett Weaver unites the world in spirit.”*  
> Please do not use this code or data for commercial gain.

![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🧭 Project Overview
A collaborative repository for structured, enriched global culture profiles.
Automates extraction, validation, and curation of cultural data for research and sharing.

## ⚙️ Setup Steps
1. Clone the repo and install dependencies:
    ```bash
    git clone <your-repo-url>
    cd Global-Culture-Project
    pip install -r requirements.txt
    ```
2. (Optional) Set up Python in VS Code for auto-formatting and linting.

## 📁 Folder Structure
```
Global-Culture-Project/
├── Global_Culture_Repository_Output.csv   # Automated, structured output
├── Global Culture Project CORE.xlsx       # Curated, human-edited view
├── scripts/
│   ├── validate_profiles.py
│   ├── parse_docx_to_csv.py
│   ├── append_culture_profile.py
│   └── nlp_quality_check.py
├── .github/workflows/
├── .vscode/
├── requirements.txt
├── .editorconfig, .gitignore, ...
└── README.md
```

## 🚀 Workflow

### 1. **Add/Update a Culture Profile**
```bash
python scripts/append_culture_profile.py
```
Follow the prompts to add or update a profile.

### 2. **Extract Profiles from .docx Files**
- Place `.docx` files in `input_docs/` (create if needed).
- Each profile should be a single line, fields separated by `|`.
```bash
python scripts/parse_docx_to_csv.py
```

### 3. **Validate Profiles**
```bash
python scripts/validate_profiles.py
```
Checks for missing columns or required fields.

### 4. **Run NLP Quality Checks**
```bash
python scripts/nlp_quality_check.py
```
Flags short or repetitive descriptions.

## ✅ Sample Profile Format (CSV)
| Culture Name | Region | Language | Description | Source |
|--------------|--------|----------|-------------|--------|
| Exampleland  | Europe | Examplean | A sample culture for demo purposes. | Example Source |
| Testonia     | Asia   | Testish   | Another example for testing.        | Test Source    |
| Samplestan   | Africa | Samplese  | Sample data for demonstration.      | Sample Source  |

## 🧠 Goals
- Automate extraction and validation of culture profiles
- Ensure data consistency and traceability
- Enable easy enrichment and curation

## 👥 Credits

**Lead Architect:** Brett Weaver  
**Collaborators:** OpenAI Codex, ChatGPT, and global community reviewers  
(Submit a PR to be listed here!)

## 📄 License
MIT License (or specify your own)

## 🧩 Culture Segmenter Tool

### Quick Start

```bash
python segmenter.py \
  --input ./data/source_data.xlsx \
  --use_gpt \
  --out_dir ./outputs \
  --out_csv full_export.csv \
  --review_csv review.csv \
  --summary_only_md summaries/
```

### Flags

| Flag               | Description                                      |
|--------------------|--------------------------------------------------|
| `--use_gpt`        | Enables OpenAI-powered enrichment                |
| `--validate`       | Checks profile completeness                      |
| `--limit`          | Limits number of cultures processed              |
| `--out_dir`        | Groups all exports into organized folders        |
| `--summary_only_md`| Outputs culture-level summaries as Markdown      |

## 📈 MkDocs-Ready Output

To preview your structured Markdown site:

Create a `mkdocs.yml`:

```yaml
site_name: Global Culture Guide
docs_dir: outputs/markdown
theme:
  name: material
```

Then:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

To build static HTML for GitHub Pages:

```bash
mkdocs build
mkdocs gh-deploy
```

📦 **GitHub Pages Setup Tip**:  
Set the GitHub Pages source to `/docs` folder (if using `mkdocs build -d docs`)  
Or use GitHub Actions for automatic deploys.

---

For formatting and linting, Ruff and Black are configured. Run:

```bash
ruff check .
ruff format .
black .
```

---

## 🚀 Features

- Batch file upload and processing (docx, xlsx, txt)
- GPT-powered enrichment (summaries, tags, section summaries)
- Interactive AgGrid review and editing before commit
- Review-only QA mode (flag, export, and approve before repo update)
- Multilingual culture title detection (with `langdetect`)
- Test/Production mode toggle (safe dry runs)
- Markdown and CSV export
- Session log viewer
- Docker containerization for portable deployment
- Modular utility functions for CLI/UI reuse
- Unit tests for UI and core logic

## 🖥️ Usage

### Run the Streamlit UI
```bash
streamlit run quick_run_ui.py
```

### Batch Upload & Review
- Select or upload multiple files in the UI
- Edit, flag, and approve segments in the AgGrid table
- Use Review-only mode for QA workflows
- Download review CSV or commit to the master repo

### Docker
```bash
docker build -t culture-ui .
docker run -p 8501:8501 culture-ui
```

### Test/Production Mode
- Use the UI toggle to switch between safe dry runs and real repo updates

### Developer Notes
- Utility functions for file discovery, metadata, and filtering are in `ui_utils.py`
- Unit tests in `tests/test_ui_utils.py`
- Install optional dependencies:
  - `pip install streamlit-aggrid langdetect`

## 🧪 Upcoming Features

- [ ] Section-level GPT summaries
- [ ] Confidence heatmaps
- [ ] Glossary of cultural keywords
- [ ] GitHub Action CI auto-validation
- [ ] Community translation support

---

Have suggestions or want to contribute? PRs welcome!
