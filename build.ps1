param()
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& .\.venv\Scripts\python.exe scripts/build.py
if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
