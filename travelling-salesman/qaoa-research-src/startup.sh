#!/bin/bash

# Simple Python Project Runner

# config.yaml and saved_result/ are resolved relative to this directory
cd "$(dirname "$0")" || exit 1

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run main.py
echo "Running main.py..."
python main.py

# Check if execution was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Execution completed successfully!"
    echo "📁 Results saved to: saved_result/experiment_data.json"
    echo "📋 Logs saved to: saved_result/app_<cities>_<timestamp>.log"
else
    echo "❌ Execution failed!"
    echo "📋 Logs saved to: saved_result/app_<cities>_<timestamp>.log"
    exit 1
fi