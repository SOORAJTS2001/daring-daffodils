# --- CONFIG ---
VENV = .venv
PYTHON = python3
POETRY = $(VENV)/bin/poetry

# --- TARGETS ---

.PHONY: all setup run clean

all: run

# Ensure venv exists
$(VENV)/bin/activate:
	@echo "👉 Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV)

# Install Poetry inside venv if missing
$(POETRY): $(VENV)/bin/activate
	@echo "👉 Ensuring Poetry is installed..."
	@. $(VENV)/bin/activate && \
		(if ! command -v poetry >/dev/null 2>&1; then \
			curl -sSL https://install.python-poetry.org | $(PYTHON) -; \
		fi)

setup: $(POETRY)
	@echo "👉 Installing dependencies..."
	@. $(VENV)/bin/activate && poetry install --no-root

run: setup
	@echo "👉 Running uvicorn server..."
	@. $(VENV)/bin/activate && python app.py

clean:
	@echo "🧹 Cleaning up..."
	@rm -rf $(VENV)
