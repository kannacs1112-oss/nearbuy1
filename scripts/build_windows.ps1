$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean NEARBUY.spec
Write-Host "Build complete: dist\\NEARBUY\\NEARBUY.exe" -ForegroundColor Green
