@echo off
REM Dictationer GUI Launcher - Uses Virtual Environment
REM This ensures all dependencies from venv are available

echo Dictationer - Voice Recording System
echo ==================================================
echo Starting GUI with virtual environment...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then install dependencies: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment and run GUI
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.
python gui_main.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] GUI exited with error code %errorlevel%
    pause
)