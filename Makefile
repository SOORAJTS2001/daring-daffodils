# --- CONFIG ---
SHELL := powershell.exe
.SHELLFLAGS := -Command
VENV = .venv
PYTHON = python
POETRY = $(VENV)/Scripts/poetry

# --- TARGETS ---

.PHONY: all setup run clean

all: run

# Ensure venv exists
$(VENV)/Scripts/activate:
	@echo "👉 Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV)

# Install Poetry inside venv if missing
$(POETRY): $(VENV)/Scripts/activate
	@echo "👉 Ensuring Poetry is installed..."
	@. $(VENV)/Scripts/pip install poetry

setup: $(POETRY)
	@echo "👉 Installing dependencies..."
	@. $(POETRY) install --no-root

run: setup
	@echo "👉 Running uvicorn server..."
	@$(VENV)/Scripts/python app.py

clean:
	@echo "🧹 Cleaning up..."
	@rm -rf $(VENV)
