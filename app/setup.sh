#!/bin/bash

# Script should ideally be run from the project root.
# This script is located in app/, so we adjust paths accordingly or cd.

# Ensure we are in the project root directory
# This assumes the script is in a subdirectory (e.g., 'app') of the project root.
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
echo "🚀 Starting Fionntán setup in project root: ${PROJECT_ROOT}"

# --- Check and attempt to install pg_config if missing (Fedora specific) ---
if ! command -v pg_config &> /dev/null
then
    echo "⚠️  pg_config command not found."
    # Check if running on Fedora (this is a basic check, could be more robust)
    if [ -f /etc/fedora-release ]; then
        echo "Fedora detected. Attempting to install PostgreSQL development libraries..."
        echo "You might be prompted for your sudo password."
        sudo dnf install -y postgresql-devel python3-devel gcc || {
            echo "❌ Failed to install PostgreSQL development libraries automatically via dnf."
            echo "Please install them manually: sudo dnf install postgresql-devel python3-devel gcc"
            echo "Then re-run this setup script."
            exit 1
        }
        # Verify again
        if ! command -v pg_config &> /dev/null; then
            echo "❌ pg_config still not found after attempting installation."
            exit 1
        else
            echo "✅ PostgreSQL development libraries seem to be installed."
        fi
    else
        echo "This script can only attempt automatic installation of pg_config dependencies on Fedora."
        echo "Please install PostgreSQL development headers, python3-devel, and gcc (or equivalents) for your OS manually."
        echo "Then re-run this setup script."
        exit 1
    fi
fi
# --- End of pg_config check ---

# Create virtual environment in the project root if it doesn't exist
VENV_DIR="./venv"
if [ ! -d "${VENV_DIR}" ]; then
  echo "🔧 Creating virtual environment '${VENV_DIR}' with Python 3.12..."
  python3.12 -m venv "${VENV_DIR}" || {
      echo "❌ Failed to create virtual environment. Make sure Python 3.12 is installed and accessible."
      exit 1
  }
fi

# Activate the virtual environment
echo "🐍 Activating virtual environment..."
source "${VENV_DIR}/bin/activate" || {
    echo "❌ Failed to activate virtual environment."
    exit 1
}

# Upgrade pip, setuptools, and wheel
echo "⬆️  Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt (path relative to project root)
REQUIREMENTS_FILE="./app/requirements.txt" # Assuming requirements.txt is inside the 'app' folder

if [ -f "${REQUIREMENTS_FILE}" ]; then
  echo "📦 Installing dependencies from ${REQUIREMENTS_FILE}..."
  pip install -r "${REQUIREMENTS_FILE}" || {
    echo "❌ Failed to install Python dependencies from ${REQUIREMENTS_FILE}. See errors above."
    exit 1
  }
else
  echo "❌ Requirements file not found at ${REQUIREMENTS_FILE}"
  exit 1
fi

# Set environment variables for running the app FROM THE PROJECT ROOT
export FLASK_APP=./main.py # Assuming main.py is in the project root
export FLASK_ENV=development
export PYTHONPATH=${PROJECT_ROOT}:${PYTHONPATH} # Add project root to PYTHONPATH

echo ""
echo "✅ Fionntán - Development Environment Setup Complete!"
echo "Your virtual environment '${VENV_DIR}' is active."
echo "To run the application (from the project root '${PROJECT_ROOT}'):"
echo "   python main.py"
echo ""
echo "To run tests (from the project root '${PROJECT_ROOT}'):"
echo "   python -m pytest"
echo "   python -m pytest tests/your_test_file.py"
echo ""
