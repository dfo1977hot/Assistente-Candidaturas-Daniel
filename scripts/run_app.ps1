$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$desktopEntryPoint = Join-Path $projectRoot "acd\desktop.py"

if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "Virtual environment não encontrada. Crie-a e instale o projeto com: .\.venv\Scripts\python.exe -m pip install -e ."
    exit 1
}

if (-not (Test-Path -LiteralPath $desktopEntryPoint)) {
    Write-Error "Módulo de inicialização acd.desktop não encontrado em: $desktopEntryPoint"
    exit 1
}

Push-Location $projectRoot
try {
    & $python -m acd.desktop
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
