#!/bin/bash
# Script to set up virtual environment on Linux/Mac

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Setup complete! Virtual environment is activated."
echo "To activate it in the future, run: source venv/bin/activate"

