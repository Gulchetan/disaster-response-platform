# One-time setup: venv + deps (works behind SSL-inspecting proxies) + migrations hint
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtualenv (Python 3.10)..."
    py -3.10 -m venv .venv
}

$py = ".\.venv\Scripts\python.exe"
$pip = ".\.venv\Scripts\pip.exe"

Write-Host "Upgrading pip..."
& $py -m pip install --upgrade pip `
    --trusted-host pypi.org `
    --trusted-host pypi.python.org `
    --trusted-host files.pythonhosted.org

Write-Host "Installing requirements..."
& $pip install -r requirements.txt `
    --trusted-host pypi.org `
    --trusted-host pypi.python.org `
    --trusted-host files.pythonhosted.org

$env:PYTHONPATH = "."
Write-Host ""
Write-Host "Done. Next commands (always use the venv python):"
Write-Host "  .\.venv\Scripts\python.exe -m alembic upgrade head"
Write-Host "  .\.venv\Scripts\python.exe -m scripts.seed_data"
Write-Host "  .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload"
