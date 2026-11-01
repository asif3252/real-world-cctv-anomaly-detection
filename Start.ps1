$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    $localPython = Join-Path $env:LOCALAPPDATA 'Python/bin/python.exe'
    if (Test-Path $localPython) {
        & $localPython -m venv .venv
    } else {
        py -3 -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 or 3.12 from python.org, including the Python launcher, then retry.' }
}
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check internet connectivity.' }
& ./.venv/Scripts/python.exe app.py
Read-Host 'Press Enter to close'

