#!/bin/bash
set -e  # Exit on any error

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Installing Playwright browsers..."
python -m playwright install chromium

echo "Installing Playwright system dependencies..."
python -m playwright install-deps chromium

echo "Build completed successfully!"