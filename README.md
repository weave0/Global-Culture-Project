# 🌍 Global Culture Project

## 📌 Overview

The Global Culture Project automates the enrichment, analysis, and exploration of cultural profiles across the world. Using AI-powered enrichment, structured data pipelines, and an interactive viewer, the system delivers a complete cultural intelligence suite out of the box.

---

## ⚙️ Setup Instructions

### 1. Bootstrap the Environment

Run one of the following:

#### Windows PowerShell

```powershell
./bootstrap_env.ps1
```

#### macOS/Linux Bash

```bash
./bootstrap_env.sh
```

This will install dependencies from [requirements.txt](requirements.txt) and prepare folders.

### Notes for Windows Users

- Ensure you have administrative privileges to run PowerShell commands.
- If you encounter issues with `dxdiag` or other commands, verify the paths and permissions.

### 2. Optional Autopilot Mode

Queue tasks in autopilot_commands.txt, then run:

```bash
python autopilot_agent.py
```

## 📁 Project Structure

| Folder              | Purpose                                      |
|---------------------|----------------------------------------------|
| parsed_output/      | Raw or partially processed cultural profiles |
| enriched_output/    | AI-enriched profiles (by language code)      |
| logs/               | Timestamps and enrichment logs              |
| streamlit_app/      | Viewer UI and supporting modules            |
| scripts/            | Core and utility Python scripts             |
| unused/             | Archived or deprecated assets               |

## 🚀 One-Command Automation

### Windows

```cmd
run_everything.bat
```

### macOS/Linux

```bash
./run_everything.sh
```

### Default Behavior

When no arguments are provided, the script will:

- Enrich all cultural profiles using GPT-4.
- Generate universal_catalog.json, .csv, .html, and .md catalog files.
- Launch the Streamlit viewer (viewer_refactored.py).

## 🛠️ Manual Control

### Enrich Profiles Only

```bash
python enrich_education_profiles.py --input parsed_output --output enriched_output --limit 5 --dry-run
```

### Generate Catalog Only

```bash
python generate_universal_catalog.py
```

### Launch Viewer

```bash
streamlit run viewer_refactored.py
```

## 🧠 Features

- **AI Enrichment**: Auto-populates cultural education fields using OpenAI GPT.
- **Multi-format Catalogs**: Output .json, .csv, .html, .md.
- **Progress Tracking**: Enrichment summaries with token usage & completion %.
- **Interactive Viewer**: Filter, search, and export culture profiles.
- **Admin Editing**: Modify .json entries live in the UI (with history).

## 🔍 Advanced Options

- `--dry-run` — simulate enrichment without saving changes.
- `--limit` — control how many files are processed at once.
- `--fields` — enrich only selected fields (comma-separated).

## 🗂️ Logs & Backup

Enriched entries are backed up to:

`enriched_output/backup/`

Summary logs are saved as:

- `enrichment_summary.json`
- `enrichment_summary.csv`

Token usage is printed for every GPT call.

## 📈 Future Enhancements

- Smart change detection to skip already-complete files.
- Failsafe retry mechanism with cache.
- Automatic viewer launch in browser post-enrichment.
- Language tag mapping diagnostics.

## 🤝 Contributing

Fork the repo, make your changes in a branch, and submit a pull request.

- Please format with black or follow existing conventions.
- Document new functions and user-facing features.

## 🧾 License

MIT License.
© [Your Org/Team Name Here]
