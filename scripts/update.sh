#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "Updating RedForge Production Suite..."
echo "========================================="

# Pull git if repository
if [ -d .git ]; then
    echo "[*] Pulling latest git updates..."
    git pull origin main
fi

# Update packages
if [ -d venv ]; then
    echo "[*] Upgrading pip dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install .
else
    echo "Warning: No virtual environment (venv) detected. Run scripts/install.sh instead."
fi

echo "========================================="
echo "RedForge successfully updated!"
echo "========================================="
