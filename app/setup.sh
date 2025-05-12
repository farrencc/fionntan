#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Create virtual environment in the parent directory if it doesn't exist
if [ ! -d "../venv" ]; then
  echo "🔧 Creating virtual environment..."
  python3.12 -m venv ../venv
fi

# Activate the virtual environment
source ../venv/bin/activate

# Upgrade pip, setuptools, and wheel
echo "⬆️  Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
if [ -f requirements.txt ]; then
  echo "📦 Installing dependencies from requirements.txt..."
  pip install -r requirements.txt || {
    echo "❌ Failed to install dependencies."
    return 1
  }
else
  echo "❌ requirements.txt not found in $(pwd)"
  return 1
fi

# Set environment variables
export FLASK_APP=../main.py
export FLASK_ENV=development
export PYTHONPATH=$(pwd)/..:$PYTHONPATH

echo "✅ Fionntan - Development Environment Ready"
echo "Run 'source venv/bin/activate' and then 'python main.py' to start the application."
