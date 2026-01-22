@echo off
REM Exit immediately on error
setlocal enabledelayedexpansion
set venv_name=.venv

REM Check if the virtual environment exists
if exist "%venv_name%" (
    echo Virtual environment "%venv_name%" already exists. Reinstalling Packages...
    python -m pip install -r requirements.txt
    exit /b 1
)

REM Create the Python virtual environment
python -m venv "%venv_name%"
if errorlevel 1 (
    echo Failed to create virtual environment.
    exit /b 1
)

REM Activate the virtual environment
call "%venv_name%\Scripts\activate.bat"

REM Upgrade pip
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    exit /b 1
)

REM Install required packages
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install packages.
    exit /b 1
)

echo Successfully created virtual environment
endlocal