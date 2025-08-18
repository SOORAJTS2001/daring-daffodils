# setup_and_run.ps1

# --- Step 0: Set paths ---
$venvPath = ".\.venv"
$activateScript = "$venvPath\Scripts\Activate.ps1"

# --- Step 1: Check for Python ---
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $python) {
        Write-Host "❌ Python not found. Please install Python 3.10+ from https://www.python.org/downloads/windows/"
        exit 1
    }
}

Write-Host "✅ Python found at $($python.Path)"

# --- Step 2: Create virtual environment ---
if (-not (Test-Path $venvPath)) {
    Write-Host "👉 Creating virtual environment..."
    & $python.Path -m venv $venvPath
} else {
    Write-Host "✅ Virtual environment already exists"
}

# --- Step 3: Activate virtual environment ---
if (-not (Test-Path $activateScript)) {
    Write-Host "❌ Activation script not found!"
    exit 1
}

# Function to run commands inside venv
function Run-InVenv($cmd) {
    & $activateScript
    Invoke-Expression $cmd
}

# --- Step 4: Ensure Poetry is installed ---
$poetry = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetry) {
    Write-Host "👉 Installing Poetry..."
    Invoke-Expression "& $python.Path -c `"$(Invoke-WebRequest -UseBasicParsing https://install.python-poetry.org).Content`""
} else {
    Write-Host "✅ Poetry already installed"
}

# --- Step 5: Install dependencies ---
Write-Host "👉 Installing dependencies..."
Run-InVenv "poetry install"

# --- Step 6: Run main.py ---
Write-Host "👉 Running main.py..."
Run-InVenv "python app.py"
