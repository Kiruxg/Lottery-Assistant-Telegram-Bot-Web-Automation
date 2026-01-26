@echo off
REM Lottery Assistant - Windows Batch Script
REM Quick launcher for common tasks

if "%1"=="test" (
    echo Running system tests...
    python main.py test
    goto :end
)

if "%1"=="check" (
    echo Running jackpot check...
    python main.py check
    goto :end
)

if "%1"=="schedule" (
    echo Starting scheduled monitoring...
    python main.py schedule
    goto :end
)

if "%1"=="setup" (
    echo Running setup...
    python setup.py
    goto :end
)

echo Usage:
echo   run.bat test      - Test all components
echo   run.bat check     - Run a single check
echo   run.bat schedule  - Start scheduled monitoring
echo   run.bat setup     - Run setup checks

:end
pause
