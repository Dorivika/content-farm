# Faceless Content Farm - Windows Setup
$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..
Write-Host "=== Faceless Content Farm Setup ===" -ForegroundColor Cyan

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

$dirs = @(
    "data", "data/logs",
    "outputs/audio", "outputs/subtitles", "outputs/videos",
    "outputs/packages/youtube", "outputs/packages/tiktok", "outputs/packages/instagram",
    "assets/backgrounds", "assets/fonts", "assets/music", "assets/screen_recordings"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "Initializing database..." -ForegroundColor Yellow
python -m src init-db

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Copy .env.example to .env and fill in your keys"
Write-Host "  2. Place service_account.json in config/"
Write-Host "  3. Share your Google Sheet with the service account email"
Write-Host "  4. Run: python -m src generate-ideas"
Write-Host ""
Write-Host "To test without API keys:"
Write-Host "  python -m src generate-ideas  (uses sample data)"
Write-Host ""
