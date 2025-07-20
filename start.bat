@echo off
REM Dictationer GUI Launcher - Uses Virtual Environment
REM This ensures all dependencies from venv are available

REM Set custom window title and red color theme
TITLE Dictationer-CLI
COLOR 0C

REM Display header with enhanced visuals
echo.
echo ============================================================
echo                  DICTATIONER-CLI
echo              Voice Recording System
echo ============================================================
echo.
echo Starting GUI with virtual environment...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo.
    powershell write-host -fore White -back Red " ERROR: Virtual environment not found! "
    echo.
    echo Please run the following commands:
    echo   1. python -m venv venv
    echo   2. venv\Scripts\pip install -r requirements.txt
    echo.
    echo ============================================================
    pause
    exit /b 1
)

REM Activate virtual environment and run GUI
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
powershell write-host -fore Green "[OK] Virtual environment activated"
echo.
echo [*] Launching Dictationer GUI...
echo ============================================================
echo.
python gui_main.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    powershell write-host -fore White -back Red " ERROR: GUI exited with error code %errorlevel% "
    echo.
    echo Please check the error messages above.
    echo ============================================================
    pause
) else (
    REM Success - restore normal colors before exit
    COLOR 07
)