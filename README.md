# Faceless Content Farm

Windows-first Python foundation for a human-approved short-form content workflow.

The MVP is for a faceless brand about practical AI workflows for founders, operators, freelancers, small businesses, and technical builders. It generates original ideas and routes them through approval, scripting, voiceover, rendering, and packaging steps. It does not scrape social platforms, automate fake engagement, send spam, or auto-post.

## Phase 1 Scope

- Repository scaffold and Windows helper scripts
- Environment and YAML configuration
- Pydantic data models
- SQLite local state
- Google Sheets service-account integration
- Typer CLI commands for database initialization and backlog checks
- Focused tests for models and database behavior

## Setup on Windows

```powershell
cd C:\Vivek\git-local-repos\content-farm\faceless-content-farm
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m src init-db
pytest
```

## Google Sheets Setup

1. Create a Google Cloud service account.
2. Download its JSON key to `config/service_account.json`.
3. Share your Google Sheet with the service account email.
4. Set `GOOGLE_SHEET_ID` in `.env`.
5. Ensure the tab named by `GOOGLE_SHEET_TAB` exists, defaulting to `Ideas`.

The pipeline reads and writes only the core workflow columns. Analytics columns can exist in the sheet for manual tracking and are ignored by the code.

## CLI

```powershell
python -m src init-db
python -m src check-backlog
```

## Phase 2 Preview

Phase 2 should add Gemini-backed ideation, prompt orchestration, script generation commands, approval workflow commands, and synchronization between SQLite and Google Sheets.
