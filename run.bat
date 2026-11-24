@echo off
setlocal
set PYTHON_EXE=e:\ML101\single-target-multicam\.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo ========================================================================
echo  Single-Target Multi-Camera Vehicle Tracking (CityFlow Benchmark)
echo ========================================================================
echo.
echo Select an option:
echo  1. Run Benchmark (Proposed Adaptive Method)
echo  2. Run All 4 Baselines & Comparative Plots
echo  3. Run Interactive Target Selection (OpenCV GUI)
echo  4. Run Unit and Integration Test Suite
echo  5. Launch Interactive Web Dashboard
echo  6. Inspect Dataset
echo  7. Exit
echo.

set /p OPTION="Enter choice (1-7): "

if "%OPTION%"=="1" (
    "%PYTHON_EXE%" app/main.py --mode benchmark --method proposed_adaptive --target 1 --camera c001
) else if "%OPTION%"=="2" (
    "%PYTHON_EXE%" evaluation/benchmark.py
    "%PYTHON_EXE%" evaluation/visualization.py
) else if "%OPTION%"=="3" (
    "%PYTHON_EXE%" app/main.py --mode interactive --target 1 --camera c001
) else if "%OPTION%"=="4" (
    "%PYTHON_EXE%" -m pytest tests/test_pipeline.py -v
) else if "%OPTION%"=="5" (
    "%PYTHON_EXE%" app/dashboard.py
) else if "%OPTION%"=="6" (
    "%PYTHON_EXE%" data/dataset_inspection.py
)

pause
