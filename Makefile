.DEFAULT_GOAL := help

# Executable paths
VENV_BIN := .venv/bin
PYTHON   := $(if $(wildcard $(VENV_BIN)/python), $(VENV_BIN)/python, python3)
PYTEST   := $(if $(wildcard $(VENV_BIN)/pytest), $(VENV_BIN)/pytest, pytest)
UVICORN  := $(if $(wildcard $(VENV_BIN)/uvicorn), $(VENV_BIN)/uvicorn, uvicorn)
STREAMLIT:= $(if $(wildcard $(VENV_BIN)/streamlit), $(VENV_BIN)/streamlit, streamlit)

.PHONY: help up down test api ui dashboard dev pipeline status

## Display available commands
help:
	@echo "Available commands:"
	@echo ""
	@echo "  make dev        Run both FastAPI and Streamlit concurrently"
	@echo "  make api        Start the FastAPI REST backend server"
	@echo "  make ui         Start the Streamlit customer review UI"
	@echo "  make dashboard  Start the Streamlit analytical metrics dashboard"
	@echo "  make test       Run the complete automated test suite"
	@echo "  make up         Start the MongoDB container (Docker)"
	@echo "  make down       Stop the MongoDB container"
	@echo "  make status     Check status of Docker containers"
	@echo "  make pipeline   Run data pipeline (prepare -> ingest -> train -> predict)"
	@echo ""

## Start MongoDB in background
up:
	docker compose up -d

## Stop MongoDB container
down:
	docker compose down

## Check MongoDB container status
status:
	docker compose ps

## Run automated test suite
test:
	$(PYTEST) -v

## Start FastAPI backend server with auto-reload
api:
	$(UVICORN) api.main:app --reload --app-dir src

## Start Streamlit customer review UI
ui:
	$(STREAMLIT) run src/interface/app.py

## Start Streamlit analytical metrics dashboard (V1)
dashboard: up
	$(STREAMLIT) run src/interface/dashboard.py

## Run both API and UI concurrently in parallel
dev: up
	@echo "Starting backend API and web interface..."
	@$(MAKE) -j 2 api ui

## Run data pipeline (prepare -> ingest -> train -> predict)
pipeline: up
	$(PYTHON) run_pipeline.py
