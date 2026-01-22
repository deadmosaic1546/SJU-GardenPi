#!/usr/bin/env bash
set -e  # exit on any errors

venv_name=".venv"

# Check if the virtual environment exists
if [ -d "$venv_name" ]; then
    echo "Virtual environment '$venv_name' already exists. Reinstalling Packages."
    "$venv_name/bin/pip" install -r requirements.txt
    exit 1
fi

# Create the python virtual environment
python3 -m venv "$venv_name"
source "$venv_name/bin/activate"
"$venv_name/bin/pip" install --upgrade pip

# Install packages to the virtual environment
"$venv_name/bin/pip" install -r requirements.txt

echo "Successfully created virtual environment"