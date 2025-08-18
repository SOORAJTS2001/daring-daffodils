# setup.ps1
# Failsafe script for Windows to create venv, install Poetry, install deps, and run app.py

$ErrorActionPreference = "Stop"

# --- CONFIG ---
$VENV_DIR = ".venv"
$PYTHON = (Get-Command python3 -ErrorAction SilentlyContinue).Source
if (-not $PYTHON) {
    $PYTHON = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PYTHON) {
    Write-Host "❌ Python 3 not found. Please install Python 3.8+ or higher." -ForegroundColor Red
    exit 1
}

# --- FUNCTIONS ---
function Log($msg) { Write-Host "👉 $msg" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "❌ $msg" -ForegroundColor Red; exit 1 }

# --- CREATE VENV IF NEEDED ---
if (-not (Test-Path $VENV_DIR)) {
    Log "Creating virtual environment in $VENV_DIR..."
    & $PYTHON -m venv $VENV_DIR
}

# --- ACTIVATE VENV ---
$activate = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (-not (Test-Path $activate)) {
    Fail "Virtual environment activation script not found at $activate"
}
. $activate
Log "Virtual environment activated."

# --- INSTALL POETRY IF MISSING ---
$poetry = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetry) {
    Log "Installing Poetry..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | & $PYTHON -
    $env:Path += ";$env:USERPROFILE\.local\bin"
    $poetry = Get-Command poetry -ErrorAction SilentlyContinue
    if (-not $poetry) {
        Fail "Poetry installation failed. Add $env:USERPROFILE\.local\bin to PATH manually."
    }
}
Log "Poetry available at $($poetry.Source)"

# --- INSTALL DEPENDENCIES ---
Log "Installing dependencies..."
poetry install --no-root

# --- RUN APP ---
Log "Running app.py..."
python app.py
