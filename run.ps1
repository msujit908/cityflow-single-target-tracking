<#
.SYNOPSIS
    Single-Target Multi-Camera Vehicle Tracking (CityFlow Benchmark) Runner
.DESCRIPTION
    Convenience PowerShell launcher for running benchmarks, interactive ROI mode,
    tests, or the interactive web dashboard.
.EXAMPLE
    .\run.ps1 -Action benchmark -Method proposed_adaptive
    .\run.ps1 -Action interactive -Camera c001 -Target 1
    .\run.ps1 -Action test
    .\run.ps1 -Action dashboard
#>

param (
    [ValidateSet("benchmark", "interactive", "all-baselines", "test", "dashboard", "inspect")]
    [string]$Action = "benchmark",
    [string]$Method = "proposed_adaptive",
    [string]$Camera = "c001",
    [int]$Target = 1,
    [string]$PythonExe = "e:\ML101\single-target-multicam\.venv\Scripts\python.exe"
)

# Resolve python
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " Single-Target Multi-Camera Vehicle Tracking (CityFlow Benchmark)" -ForegroundColor Green
Write-Host " Action: $Action | Method: $Method | Target: $Target | Camera: $Camera" -ForegroundColor Yellow
Write-Host "========================================================================" -ForegroundColor Cyan

switch ($Action) {
    "inspect" {
        & $PythonExe data/dataset_inspection.py
    }
    "benchmark" {
        & $PythonExe app/main.py --mode benchmark --method $Method --target $Target --camera $Camera
    }
    "interactive" {
        & $PythonExe app/main.py --mode interactive --method $Method --target $Target --camera $Camera
    }
    "all-baselines" {
        & $PythonExe evaluation/benchmark.py
        & $PythonExe evaluation/visualization.py
    }
    "test" {
        & $PythonExe -m pytest tests/test_pipeline.py -v
    }
    "dashboard" {
        Write-Host "[+] Launching Web Dashboard at http://localhost:8088/ ..." -ForegroundColor Green
        & $PythonExe app/dashboard.py
    }
}
