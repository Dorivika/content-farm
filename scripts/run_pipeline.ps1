$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..
& .\.venv\Scripts\Activate.ps1
python -m src run-daily
