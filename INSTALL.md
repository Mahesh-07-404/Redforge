# RedForge Installation Guide

This guide explains how to install RedForge for local development and CLI operations.

---

## System Requirements

* **OS**: Kali Linux, Debian, Ubuntu, macOS, or Windows (WSL2)
* **Python**: Version 3.12 or higher
* **Node.js**: Version 18 or higher (only required for the React Dashboard)
* **External Scanners** (Optional): `nmap`, `git`, `curl`

---

## Local Installation

### 1. Run the installation script
The easiest way is to run the automated installation script:
```bash
./scripts/install.sh
```
This script sets up a virtual environment (`venv`) and installs the project dependencies.

### 2. Manual setup
Alternatively, install the package manually:
```bash
# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install package
pip install --upgrade pip
pip install -e .
```

### 3. Setup Configuration
Generate a `.env` configuration file:
```bash
cp .env.development .env
```
Edit the `.env` file to configure port settings, log levels, and your LLM API keys.

---

## Running RedForge

### Start Backend API Gateway
```bash
source venv/bin/activate
uvicorn redforge.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### Start CLI Console Interface
```bash
source venv/bin/activate
redforge
```
