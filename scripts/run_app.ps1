$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$app = Join-Path $projectRoot "app.py"

if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "Virtual environment não encontrada. Crie-a e instale o projeto com: .\.venv\Scripts\python.exe -m pip install -e ."
    exit 1
}
if (-not (Test-Path -LiteralPath $app)) {
    Write-Error "Arquivo app.py não encontrado na raiz do projeto."
    exit 1
}

& $python $app
exit $LASTEXITCODE
