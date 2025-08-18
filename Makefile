# --- CONFIG ---
VENV = .venv
PYTHON = python
ifeq ($(OS),Windows_NT)
    ENVPYTHON := .venv/Scripts/python
    POETRY := .venv/Scripts/poetry
	PIP := .venv/Scripts/pip
else
    ENVPYTHON := .venv/bin/python
    POETRY := .venv/bin/poetry
	PIP := .venv/bin/pip
endif

# --- TARGETS ---

.PHONY: all setup run clean

all: run

# Ensure venv exists
$(VENV):
	@echo "👉 Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV)

# Install Poetry inside venv if missing
$(POETRY): $(VENV)
	@echo "👉 Ensuring Poetry is installed..."
	@$(PIP) install poetry

setup: $(POETRY)
	@echo "👉 Installing dependencies..."
	@$(POETRY) install --no-root

run: setup
	@echo "👉 Running uvicorn server..."
	@$(ENVPYTHON) app.py

clean:
	@echo "🧹 Cleaning up..."
	@rm -rf $(VENV)
