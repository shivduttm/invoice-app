#!/bin/bash

echo "Setting up environment..."

# Ensure virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
fi

# Activate virtual environment
source venv/Scripts/activate  # For Windows Git Bash
# source venv/bin/activate     # For Linux/Mac

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations (if using Flask-Migrate)..."
flask db upgrade || echo "No migrations to apply."

echo "Collecting static files..."
mkdir -p static  # Ensure static folder exists

echo "Build complete!"
