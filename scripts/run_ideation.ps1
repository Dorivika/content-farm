$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot\..
.\.venv\Scripts\python.exe -m src check-backlog
