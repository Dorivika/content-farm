$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
.\.venv\Scripts\python.exe -m src init-db
