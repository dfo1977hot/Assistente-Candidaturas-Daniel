param(
    [ValidateSet("Fast", "Full")]
    [string]$Gate = "Fast",
    [string[]]$Tests = @()
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

Set-Location $projectRoot

function Invoke-Check([string[]]$Arguments) {
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Get-CoverageMetrics([string]$ReportPath) {
    $parserPath = Join-Path $PSScriptRoot "coverage_report.py"
    $metricsJson = & $python $parserPath $ReportPath

    if ($LASTEXITCODE -ne 0) {
        throw "Coverage report parsing failed for '$ReportPath'."
    }

    try {
        return $metricsJson | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw "Coverage report parsing failed: the metrics payload is invalid."
    }
}

function Update-MonotonicBaseline(
    [psobject]$Baseline,
    [decimal]$GlobalCoverage,
    [decimal]$BranchCoverage,
    [string]$BaselinePath
) {
    $promoted = $false

    if ($GlobalCoverage -gt [decimal]$Baseline.global_coverage) {
        $Baseline.global_coverage = $GlobalCoverage
        $promoted = $true
    }

    if ($BranchCoverage -gt [decimal]$Baseline.branch_coverage) {
        $Baseline.branch_coverage = $BranchCoverage
        $promoted = $true
    }

    if ($promoted) {
        $Baseline.approved_on = (Get-Date -Format "yyyy-MM-dd")
        $baselineJson = $Baseline | ConvertTo-Json -Depth 4
        $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($BaselinePath, $baselineJson, $utf8WithoutBom)
        Write-Host "Coverage baseline promoted: global=$($Baseline.global_coverage)%; branches=$($Baseline.branch_coverage)%."
    }
}

Invoke-Check @("-m", "ruff", "check", ".")
Invoke-Check @("-m", "compileall", "acd")

if ($Gate -eq "Fast") {
    if ($Tests.Count -eq 0) {
        Write-Error "Fast gate requires one or more targeted tests via -Tests."
        exit 2
    }
    Invoke-Check (@("-m", "pytest") + $Tests)
    exit 0
}

$baselinePath = Join-Path $projectRoot "quality\coverage-baseline.json"
$reportPath = Join-Path $projectRoot ".coverage-full.json"
$tempPath = Join-Path $projectRoot ".coverage-runtime"
$baseline = Get-Content $baselinePath -Raw | ConvertFrom-Json

Invoke-Check @(
    "-m", "pytest", "--cov=acd", "--cov-report=json:$reportPath",
    "--cov-fail-under=0", "--basetemp", $tempPath
)

$metrics = Get-CoverageMetrics $reportPath
$actual = [decimal]$metrics.global_coverage
$branchCoverage = [decimal]$metrics.branch_coverage
$minimum = [decimal]$baseline.global_coverage

if ($actual -lt $minimum) {
    Write-Error "Coverage regression: $actual% is below approved baseline $minimum%."
    exit 1
}

Write-Host "Coverage report: global=$actual%; branches=$branchCoverage%."
Write-Host "Coverage baseline check passed: $actual% >= $minimum%."
Update-MonotonicBaseline $baseline $actual $branchCoverage $baselinePath
