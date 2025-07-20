#!/bin/bash
# Dictationer GUI Launcher - Uses Virtual Environment
# This ensures all dependencies from venv are available

echo "🎤 Dictationer - Voice Recording System"
echo "=================================================="
echo "Starting GUI with virtual environment..."
echo

# Check if virtual environment exists
if [ ! -f "venv/bin/python" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then install dependencies: venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment and run GUI
echo "Activating virtual environment..."
source venv/bin/activate
echo "Virtual environment activated"
echo
python gui_main.py

# Check exit code
if [ $? -ne 0 ]; then
    echo
    echo "❌ GUI exited with error code $?"
    read -p "Press Enter to continue..."
fi