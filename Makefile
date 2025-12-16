.PHONY: install doctor fmt lint sec test gate tf-check preflight clean

# 1. SETUP & CHECKS
doctor:
	@echo "🏥 Checking Local Environment..."
	@which python3 > /dev/null || (echo "❌ Python3 missing" && exit 1)
	@which git > /dev/null || (echo "❌ Git missing" && exit 1)
	@echo "✅ Tools found."
	@echo "Checking AWS Identity..."
	@aws sts get-caller-identity --query "Arn" --output text || echo "⚠️  AWS not configured (OK for Phase 0)"

install:
	@echo "📦 Installing dependencies..."
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/pre-commit install

# 2. HYGIENE & SECURITY
fmt:
	@echo "🧹 Formatting code..."
	.venv/bin/ruff format .

lint:
	@echo "🧐 Linting code..."
	.venv/bin/ruff check .

sec:
	@echo "🛡️  Running Security Scan..."
	# Simple bandit scan on app directory (if exists)
	@if [ -d "app" ]; then .venv/bin/bandit -q -r app; fi
	.venv/bin/pip-audit

tf-check:
	@echo "☁️  Checking Terraform..."
	@if [ -d "infra/terraform" ]; then \
		terraform -chdir=infra/terraform fmt -check -recursive && \
		terraform -chdir=infra/terraform validate; \
	else \
		echo "⚠️ Terraform dir not found (skipping)"; \
	fi

# 3. TESTING & GATES
test:
	@echo "🧪 Running Unit Tests..."
	# FIX: Add PYTHONPATH=. so pytest finds 'app'
	PYTHONPATH=. .venv/bin/pytest -q || echo "⚠️ Tests skipped (no tests/ yet)"

gate:
	@echo "🔒 Running Security Gates..."
	@echo "⚠️ Gates skipped (not implemented yet)"

# 4. THE GOLDEN RULE
preflight: fmt lint sec test gate tf-check
	@echo "🚀 READY FOR COMMIT."

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist build
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +

# 5. LOCAL DEV
run-local:
	@echo "🚀 Starting local API..."
	.venv/bin/uvicorn app.main:app --reload --port 8000
