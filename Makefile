# --- CONFIG ---
PYTHON := $(shell command -v python3 || command -v python)

# Detect OS and choose correct venv activate path
ifeq ($(OS),Windows_NT)
    ACTIVATE = .venv/Scripts/activate
else
    ACTIVATE = .venv/bin/activate
endif

VENV = .venv
POETRY = $(VENV)/bin/poetry

# --- TARGETS ---

.PHONY: all setup run clean

all: run

# Ensure venv exists
$(ACTIVATE):
	@echo "👉 Creating virtual environment with $(PYTHON)..."
	@$(PYTHON) -m venv $(VENV)

# Install Poetry inside venv if missing
$(POETRY): $(ACTIVATE)
	@echo "👉 Ensuring Poetry is installed..."
	@. $(ACTIVATE) && \
		(if ! command -v poetry >/dev/null 2>&1; then \
			curl -sSL https://install.python-poetry.org | $(PYTHON) -; \
		fi)

setup: $(POETRY)
	@echo "👉 Installing dependencies..."
	@. $(ACTIVATE) && poetry install --no-root

run: setup
	@echo "👉 Running uvicorn server..."
	@. $(ACTIVATE) && python app.py

clean:
	@echo "🧹 Cleaning up..."
	@rm -rf $(VENV)
