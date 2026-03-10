.PHONY: help tree init lint test run-local docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make tree        - Show key project directories"
	@echo "  make init        - Create placeholder keep files"
	@echo "  make lint        - Placeholder lint command"
	@echo "  make test        - Placeholder test command"
	@echo "  make run-local   - Placeholder local run command"
	@echo "  make docker-up   - Start docker compose services"
	@echo "  make docker-down - Stop docker compose services"

tree:
	@echo "Project structure:"
	@echo "frontend/ gateway/ services/ proto/ data/ docs/"
	@ls -la .
	@ls -la services

init:
	@mkdir -p data/videos data/models docs
	@touch data/videos/.gitkeep data/models/.gitkeep docs/.gitkeep
	@echo "Initialized placeholder files."

lint:
	@echo "TODO: add lint pipeline (python + frontend)."

test:
	@echo "TODO: add test pipeline (pytest + vitest)."

run-local:
	@echo "TODO: start gateway/services/frontend in local mode."

docker-up:
	docker compose up -d

docker-down:
	docker compose down
