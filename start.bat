@echo off
echo Checking Python installation...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Python is installed.
echo Checking required libraries...

python -c "import PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Pillow...
    python -m pip install Pillow
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Pillow!
        pause
        exit /b 1
    )
) else (
    echo Pillow is already installed.
)

python -c "import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing numpy...
    python -m pip install numpy
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install numpy!
        pause
        exit /b 1
    )
) else (
    echo numpy is already installed.
)

python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: tkinter is not available!
    echo tkinter should come with Python. You may need to reinstall Python.
    pause
    exit /b 1
) else (
    echo tkinter is available.
)

echo All dependencies are installed.
echo Starting RecolorTool...
python recolortool.py

if %errorlevel% neq 0 (
    echo Program ended with error code %errorlevel%
    pause
)
