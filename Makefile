.PHONY: help tree init check-env install-backend install-frontend lint lint-backend lint-frontend test test-backend test-frontend run-local local-up local-down local-logs update-cert docker-up docker-down docker-logs docker-restart docker-status

help:
	@echo "Available commands:"
	@echo "  make tree        - Show key project directories"
	@echo "  make init        - Create placeholder keep files"
	@echo "  make check-env   - Check local tool versions"
	@echo "  make install-backend  - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo "  make lint        - Run backend and frontend linters"
	@echo "  make test        - Run backend and frontend tests"
	@echo "  make run-local   - Placeholder local run command"
	@echo "  make local-up    - Start services in background (local dev)"
	@echo "  make local-down  - Stop all local services"
	@echo "  make local-logs  - View real-time logs"
	@echo "  make update-cert - Generate/update SSL certificates"
	@echo "  make docker-up   - Start docker compose services (后台运行)"
	@echo "  make docker-down - Stop docker compose services"
	@echo "  make docker-logs - View service logs"
	@echo "  make docker-restart - Restart services"
	@echo "  make docker-status - Check service status"

tree:
	@echo "Project structure:"
	@echo "frontend/ backend/ data/ docs/"
	@ls -la .
	@ls -la backend

init:
	@mkdir -p data/videos data/models docs
	@touch data/videos/.gitkeep data/models/.gitkeep
	@echo "Initialized placeholder files."

check-env:
	@echo "Python:" && python3 --version || true
	@echo "Node:" && node --version || true
	@echo "npm:" && npm --version || true
	@echo "Docker:" && docker --version || true

install-backend:
	@cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

install-frontend:
	@cd frontend && npm install

lint:
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend

lint-backend:
	@cd backend && . .venv/bin/activate && black --check app tests
	@cd backend && . .venv/bin/activate && isort --check-only app tests
	@cd backend && . .venv/bin/activate && flake8 app tests

lint-frontend:
	@cd frontend && npm run lint
	@cd frontend && npm run format:check

test:
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend:
	@cd backend && . .venv/bin/activate && pytest

test-frontend:
	@cd frontend && npm run test

run-local:
	@echo "本地运行命令："
	@echo "  make local-up    - 在后台启动前后端服务"
	@echo "  make local-down  - 停止所有服务"
	@echo "  make local-logs  - 查看实时日志"

local-up:
	@echo "🚀 正在启动 FireTrain 项目（本地开发模式）..."
	./scripts/start-local.sh

local-down:
	@echo "🛑 正在停止 FireTrain 项目..."
	./scripts/stop-local.sh

local-logs:
	@echo "📋 查看实时日志..."
	./scripts/logs.sh

update-cert:
	@echo "🔒 生成/更新 SSL 证书..."
	./scripts/update-cert.sh

docker-up:
	docker compose up -d
	@echo "✅ 服务已在后台启动"
	@echo "📊 查看日志：docker compose logs -f"
	@echo "🛑 停止服务：make docker-down"
	docker compose ps

docker-down:
	docker compose down
	@echo "✅ 服务已停止"

docker-logs:
	docker compose logs -f

docker-restart:
	docker compose restart
	@echo "✅ 服务已重启"

docker-status:
	docker compose ps
