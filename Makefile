# --- CONFIG ---
VENV = .venv
PYTHON = python3
ifeq ($(OS),Windows_NT)
    ENVPYTHON := $(VENV)/Scripts/python
    POETRY := $(VENV)/Scripts/poetry
	PIP := $(VENV)/Scripts/pip
else
    ENVPYTHON := $(VENV)/bin/python
    POETRY := $(VENV)/bin/poetry
	PIP := $(VENV)/bin/pip
endif

PYTHON3_OK := $(shell type -P python3)
ifeq ('$(PYTHON3_OK)','')
    PYTHON = python
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
