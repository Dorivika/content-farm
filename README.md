# Faceless Content Farm

Content automation MVP for a human-in-the-loop faceless short-form video workflow.

## 1. What This Project Does

This project helps run a practical AI workflow content brand. It generates original ideas, lets a human approve them in Google Sheets, generates scripts, creates voiceover audio, renders vertical videos, and exports manual upload packages.

It is not an auto-posting system. It does not scrape TikTok, Instagram, YouTube, LinkedIn, X, or Reddit. It does not automate fake engagement, comments, DMs, or community management.

Pipeline:

```text
Ideas -> Human Approval -> Scripts -> Voiceover -> Render -> Package -> Manual Upload
```

## 2. Windows Setup

```powershell
git clone <repo>
cd faceless-content-farm
.\scripts\setup_windows.ps1
```

If PowerShell blocks scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

FFmpeg must be installed and available on `PATH`, or configured with `FFMPEG_PATH` in `.env`.

## 3. Google Sheets Setup

1. Go to Google Cloud Console.
2. Create a project or select an existing one.
3. Enable the Google Sheets API.
4. Create a Service Account.
5. Download the JSON key and save it as `config/service_account.json`.
6. Create a Google Sheet.
7. Share the sheet with the service account email as Editor.
8. Copy the Sheet ID from the URL.
9. Create a tab named `Ideas`.
10. Add the columns below to row 1.
11. Set `GOOGLE_SHEET_ID` in `.env`.

Core columns:

```text
idea_id, date_added, source, source_url, content_pillar, target_viewer,
viewer_pain, title, hook, script_outline, suggested_visuals, tools_needed,
monetization_angle, CTA, platform_primary, platform_secondary,
ideal_length_seconds, difficulty_score, novelty_score, monetization_score,
production_speed_score, risk_score, total_score, status, assigned_to,
due_date, script_status, voiceover_status, video_status, notes
```

Manual analytics columns:

```text
published_url_youtube, published_url_tiktok, published_url_instagram,
views_24h, avg_view_duration, retention_percent, likes, comments,
shares, saves, profile_visits, link_clicks, email_signups, sales
```

The pipeline reads and writes core columns. Analytics columns are manually filled after publishing and used as context for future idea generation.

## 4. Configure .env

```powershell
Copy-Item .env.example .env
```

Fill in:

```env
GEMINI_API_KEY=
PEXELS_API_KEY=
GOOGLE_SHEET_ID=
GOOGLE_SHEET_TAB=Ideas
GOOGLE_CREDENTIALS_PATH=config/service_account.json
TTS_VOICE=en-US-GuyNeural
BACKLOG_MINIMUM=20
IDEAS_TO_GENERATE=50
DEFAULT_VIDEO_SECONDS=45
FFMPEG_PATH=ffmpeg
LOG_LEVEL=INFO
OFFLINE_MODE=false
GEMINI_IMAGE_MODEL=gemini-3.1-flash-image-preview
```

`GEMINI_API_KEY` comes from Google AI Studio. `PEXELS_API_KEY` comes from pexels.com/api. If keys are empty, the project uses deterministic sample ideas, text-only visuals, solid backgrounds, and SRT-style captions. Set `OFFLINE_MODE=true` to force local fallbacks even when Windows has API keys configured. When the Gemini key is set and offline mode is false, idea generation uses Gemini Deep Research and is gated by `BACKLOG_MINIMUM` to limit cost.

## 5. Testing Without API Keys

```powershell
$env:GEMINI_API_KEY=''
$env:GOOGLE_SHEET_ID=''
$env:OFFLINE_MODE='true'
python -m src init-db
python -m src generate-ideas
```

Get an idea ID:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/content.db'); print(c.execute('select idea_id from ideas limit 1').fetchone()[0])"
```

Then run:

```powershell
python -m src generate-script --idea-id <id>
python -m src voiceover --idea-id <id>
python -m src render --idea-id <id>
python -m src package --idea-id <id>
```

## 6. Full Workflow

```powershell
python -m src generate-ideas
```

Review ideas in Google Sheets and change approved rows to:

```text
status = Approved
```

Then run:

```powershell
python -m src pull-approved
python -m src generate-script --idea-id <id>
python -m src voiceover --idea-id <id>
python -m src render --idea-id <id>
python -m src package --idea-id <id>
```

Or run the daily orchestrator:

```powershell
python -m src run-daily
```

`run-daily` checks backlog, pulls approved rows, scripts up to 3 approved ideas, creates voiceovers for up to 3 scripted ideas, renders up to 3 voiceover-complete ideas, and packages up to 3 rendered ideas. Each item is isolated so one failure does not block the rest.

## 7. What Is NOT Automated

- Approval: a human reviews ideas in Google Sheets.
- Uploading: packages are created for manual upload.
- Analytics collection: metrics are manually entered in the Sheet.
- Thumbnail creation.
- Community management.
- Social scraping or fake engagement.

## 8. Troubleshooting

| Problem | Fix |
|---------|-----|
| PowerShell blocks scripts | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| FFmpeg not found | Install from ffmpeg.org, add to PATH, or set `FFMPEG_PATH` |
| Google auth error | Check `config/service_account.json` and verify the Sheet is shared with the service account email |
| Token/OAuth errors | This project uses service accounts, not OAuth. Delete any `token.json` |
| Gemini key missing | Get a key from Google AI Studio. The pipeline works without it using sample data |
| Deep Research costs too much | Increase `BACKLOG_MINIMUM` discipline, lower `IDEAS_TO_GENERATE`, and avoid `--force` |
| edge-tts fails | The library is unofficial. The pipeline generates silent audio as fallback |
| Render produces no video | Check FFmpeg stderr in `data/logs/pipeline.log` |
| Sheet says unable to parse range | Confirm the tab is named exactly `Ideas` or update `GOOGLE_SHEET_TAB` |

## 9. Project Structure

- `src/settings.py`: environment and `.env` settings.
- `src/logger.py`: Rich console and rotating file logging.
- `src/models.py`: Pydantic models for ideas, scripts, packages, analytics.
- `src/db.py`: SQLite persistence.
- `src/sheets.py`: Google Sheets service-account integration.
- `src/prompts.py`: YAML and Markdown prompt rendering.
- `src/idea_generator.py`: Deep Research idea generation plus offline fallback.
- `src/deep_research.py`: Gemini Interactions API wrapper.
- `src/performance_context.py`: converts historical analytics into prompt context.
- `src/script_generator.py`: Gemini script generation plus offline fallback.
- `src/voiceover.py`: edge-tts audio generation plus silent FFmpeg fallback.
- `src/captions.py`: pycaps caption overlay attempt plus structured SRT fallback.
- `src/broll.py`: Pexels vertical video search and cached b-roll downloads.
- `src/visual_generator.py`: Gemini image generation for workflow step mockups.
- `src/renderer.py`: FFmpeg vertical MP4 compositing with b-roll, mockups, captions, and audio.
- `src/package_exporter.py`: platform package text exports.
- `src/analytics.py`: CSV and SQLite event logging.
- `src/pipeline.py`: reusable pipeline actions.
- `src/orchestrator.py`: daily runner and retry logic.
- `src/cli.py`: Typer CLI.

## 10. Running Tests

```powershell
python -m pytest tests/ -v
```

## Common Commands

```powershell
python -m src init-db
python -m src check-backlog
python -m src generate-ideas --count 5
python -m src pull-approved
python -m src generate-script --idea-id <id>
python -m src voiceover --idea-id <id>
python -m src render --idea-id <id>
python -m src package --idea-id <id>
python -m src run-daily
python -m src retry-failed
```

Verify rendered video:

```powershell
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name -show_entries format=duration,size -of default=noprint_wrappers=1 outputs\videos\<id>.mp4
start outputs\videos\<id>.mp4
```
