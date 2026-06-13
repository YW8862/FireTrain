default: test

CRITICAL_TESTS = \
	tests/test_rule_engine.py \
	tests/test_scoring.py \
	tests/test_llm_scoring_service.py \
	tests/test_permission.py \
	tests/test_security.py \
	tests/test_training_service_unit.py

CRITICAL_COV_MODULES = \
	--cov=app.ai.llm_scoring_service \
	--cov=app.ai.rule_engine \
	--cov=app.ai.feedback_generator \
	--cov=app.core.security \
	--cov=app.middleware.permission \
	--cov=app.services.training_service

.PHONY: default help tree init check-env install-backend install-frontend lint lint-backend lint-frontend test test-all test-backend test-backend-all test-critical test-frontend coverage-html serve-coverage coverage-clean run-local local-up local-down local-logs update-cert docker-up docker-down docker-logs docker-restart docker-status

help:
	@echo "Available commands:"
	@echo "  make tree        - Show key project directories"
	@echo "  make init        - Create placeholder keep files"
	@echo "  make check-env   - Check local tool versions"
	@echo "  make install-backend  - Install backend dependencies"
	@echo "  make install-frontend - Install frontend dependencies"
	@echo "  make lint        - Run backend and frontend linters"
	@echo "  make test        - Run the 6 critical backend module tests"
	@echo "  make test-critical - Run the 6 critical backend module tests"
	@echo "  make test-backend-all - Run the legacy full backend test suite"
	@echo "  make test-all    - Run full backend + frontend test suites"
	@echo "  make coverage-html - Generate HTML coverage report (backend + frontend)"
	@echo "  make serve-coverage - Start local HTTP servers for both coverage reports (ports 8765/8766)"
	@echo "  make coverage-clean - Remove generated coverage artifacts (htmlcov/, coverage/)"
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
	@$(MAKE) test-critical

test-backend:
	@$(MAKE) test-critical

test-critical:
	@cd backend && . .venv/bin/activate && pytest $(CRITICAL_TESTS) $(CRITICAL_COV_MODULES) --cov-report=term-missing

test-backend-all:
	@cd backend && . .venv/bin/activate && pytest --cov=app --cov-report=term-missing

test-all: test-backend-all test-frontend
	@echo "✅ All tests (backend + frontend) completed."

test-frontend:
	@cd frontend && npm run test

coverage-html:
	@echo "📊 后端：跑全量测试并生成 HTML 覆盖率报告..."
	@cd backend && . .venv/bin/activate && pytest --cov=app --cov-report=html:htmlcov --cov-report=term-missing
	@echo "📊 前端：跑测试并生成 HTML 覆盖率报告..."
	@cd frontend && npm run test -- --coverage.reporter=text --coverage.reporter=html >/dev/null
	@echo ""
	@echo "✅ HTML 报告已生成："
	@echo "  后端：backend/htmlcov/index.html"
	@echo "  前端：frontend/coverage-html/index.html"

coverage-clean:
	@rm -rf backend/htmlcov backend/.coverage frontend/coverage-html
	@echo "🧹 已清理 coverage 产物"

serve-coverage:
	@if [ ! -d backend/htmlcov ] || [ ! -d frontend/coverage-html ]; then \
		echo "❌ 报告未生成，请先执行: make coverage-html"; exit 1; \
	fi
	@echo "🚀 启动两个 HTTP 服务（Ctrl+C 一起停）："
	@echo "  后端 http.server :8765  → backend/htmlcov/"
	@echo "  前端 http.server :8766  → frontend/coverage-html/"
	@echo ""
	@echo "📡 在开发机执行端口转发："
	@echo "  ssh -L 8765:localhost:8765 -L 8766:localhost:8766 user@<server-host>"
	@echo ""
	@echo "🌐 开发机浏览器打开："
	@echo "  http://localhost:8765/  ← 后端覆盖率"
	@echo "  http://localhost:8766/  ← 前端覆盖率"
	@echo ""
	@trap 'kill 0' INT TERM EXIT; \
		cd backend/htmlcov && python3 -m http.server 8765 & \
		cd frontend/coverage-html && python3 -m http.server 8766 & \
		wait

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
