#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "Uninstalling RedForge Production Suite..."
echo "========================================="

# Clean virtual environments
if [ -d venv ]; then
    echo "[*] Removing virtual environment..."
    rm -rf venv
fi

# Clean caches
echo "[*] Cleaning build/cache artifacts..."
rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/
find . -type d -name "__pycache__" -exec rm -rf {} +

# Optional configuration delete
read -p "Do you want to permanently delete your configuration (.env) file? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "[*] Deleting configuration (.env)..."
    rm -f .env
fi

echo "========================================="
echo "RedForge successfully uninstalled."
echo "========================================="
