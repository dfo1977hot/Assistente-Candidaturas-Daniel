$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

Set-Location $projectRoot

$checks = @(
    @{ Name = "Ruff"; Arguments = @("-m", "ruff", "check", ".") },
    @{ Name = "Compileall"; Arguments = @("-m", "compileall", "acd") },
    @{ Name = "Pytest"; Arguments = @("-m", "pytest") }
)

foreach ($check in $checks) {
    Write-Host "Executando $($check.Name)..."
    & $python @($check.Arguments)

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

exit 0
