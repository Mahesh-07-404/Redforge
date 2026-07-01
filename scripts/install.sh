#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "Installing RedForge Production Suite..."
echo "========================================="

# Verify python
if ! command -v python3 &>/dev/null; then
    echo "Error: Python3 is required."
    exit 1
fi

# Setup virtual environment
echo "[*] Setting up python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install pip dependencies
echo "[*] Installing dependencies..."
pip install --upgrade pip
pip install .

# Setup default configuration
if [ ! -f .env ]; then
    echo "[*] Generating production .env config file..."
    cat <<EOT > .env
REDFORGE_ENV=production
REDFORGE_HOST=127.0.0.1
REDFORGE_PORT=8000
REDFORGE_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
REDFORGE_RATE_LIMIT=100
EOT
fi

echo "========================================="
echo "RedForge successfully installed!"
echo "Run with: source venv/bin/activate && uvicorn redforge.api.app:app --host 127.0.0.1 --port 8000"
echo "========================================="
