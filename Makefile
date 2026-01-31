# Compliance-Aligned Data Access Gateway
# v1.0.0

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
SHELL := /bin/bash

VENV ?= .venv
BIN := $(VENV)/bin
PY := $(BIN)/python3
PIP := $(BIN)/pip

# Local (header) mode is intentionally fail-closed.
# Make targets that run the app/tests set this explicitly so review is frictionless.
LOCAL_ENV := AUTH_MODE=headers ALLOW_INSECURE_HEADERS=true

.PHONY: help bootstrap install fmt lint sec audit test gate ci verify \
	run-local smoke-local pack-lambda \
	doctor doctor-aws deploy-dev destroy-dev smoke-cloud logs-cloud \
	docker-build docker-run clean review

help:
	@echo "Targets: bootstrap install fmt lint sec audit test gate ci verify run-local smoke-local deploy-dev smoke-cloud logs-cloud docker-build docker-run clean review"

# -----------------------------------------------------------------------------
# Reviewer Empathy
# -----------------------------------------------------------------------------
review:
	@clear
	@echo "======================================================================"
	@echo "🛡️  COMPLIANCE-ALIGNED DATA ACCESS GATEWAY - REVIEWER SUMMARY"
	@echo "======================================================================"
	@echo ""
	@echo "✅  Build Status:      See CI badge (or run 'make verify')"
	@echo "🔒  Vulnerabilities:   Run 'make audit'"
	@echo "🕵️  Security Gates:    ACTIVE (Tenant Isolation, Safe Logging, etc.)"
	@echo "🏗️  Infrastructure:    Terraform + AWS Lambda (Dev Slice)"
	@echo ""
	@echo "----------------------------------------------------------------------"
	@echo "🚀  NEXT STEPS FOR REVIEWER:"
	@echo "----------------------------------------------------------------------"
	@echo "1. Run 'make verify'      -> Re-verify the full security suite."
	@echo "2. Run 'make smoke-local' -> See the API handle a request locally."
	@echo "3. Read 'docs/controls.md' -> Controls → Implementation → Evidence."
	@echo ""
	@echo "======================================================================"

# -----------------------------------------------------------------------------
# Bootstrap (fresh-machine friendly)
# -----------------------------------------------------------------------------
bootstrap:
	@# Create venv if missing
	@if [ ! -d "$(VENV)" ]; then \
		echo "🔧 Creating virtual environment at $(VENV)..."; \
		python3 -m venv $(VENV); \
	fi
	@$(PIP) install --upgrade pip
	@# Install both runtime + dev tools (reviewer-friendly)
	@$(PIP) install -r requirements-runtime.txt -r requirements-dev.txt

install: bootstrap

# -----------------------------------------------------------------------------
# Quality / Security
# -----------------------------------------------------------------------------
fmt: bootstrap
	@cd $(ROOT) && $(BIN)/ruff format .

lint: bootstrap
	@cd $(ROOT) && $(BIN)/ruff check .

# Static security checks
sec: bootstrap
	@cd $(ROOT) && $(BIN)/bandit -r app -q

# Supply-chain audit (CVE scanning) - runtime is the highest-signal set
audit: bootstrap
	@cd $(ROOT) && $(BIN)/pip-audit -r requirements-runtime.txt

test: bootstrap
	@cd $(ROOT) && $(LOCAL_ENV) $(PY) -m pytest -v

# THE Gate: one command validates the repo claims.
# Note: specific gates run with LOCAL_ENV to pass the strict startup checks
gate: bootstrap
	@cd $(ROOT) && $(BIN)/ruff check .
	@cd $(ROOT) && $(BIN)/bandit -r app -q
	@cd $(ROOT) && $(LOCAL_ENV) $(PY) -m pytest -v
	@cd $(ROOT) && $(LOCAL_ENV) $(PY) -m evals.tenant_isolation_gate
	@cd $(ROOT) && $(LOCAL_ENV) $(PY) -m evals.no_admin_leakage_gate
	@cd $(ROOT) && $(LOCAL_ENV) $(PY) -m evals.safe_logging_gate
	@cd $(ROOT) && $(BIN)/pip-audit -r requirements-runtime.txt
	@echo "✅ ALL GATES PASSED."

ci: gate

# Auditor-friendly alias (no drift)
verify: gate

# -----------------------------------------------------------------------------
# Local dev
# -----------------------------------------------------------------------------
run-local: bootstrap
	@echo "▶️  Running local (header mode) on http://127.0.0.1:8000"
	@# Disable uvicorn access logs; rely on gateway-owned app.access logs (with request_id)
	@cd $(ROOT) && $(LOCAL_ENV) $(BIN)/uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log

smoke-local: bootstrap
	@echo "▶️  Local smoke: /health and /whoami"
	@curl -s http://127.0.0.1:8000/health
	@curl -s http://127.0.0.1:8000/whoami -H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern'

# -----------------------------------------------------------------------------
# Lambda packaging / AWS dev slice
# -----------------------------------------------------------------------------
pack-lambda: bootstrap
	@rm -rf dist && mkdir -p dist
	@echo "📦 Building Lambda artifact to dist/lambda.zip"
	@cd $(ROOT) && $(PY) scripts/package_lambda.py

# Tooling checks
doctor: bootstrap
	@$(PY) -V
	@$(BIN)/ruff --version
	@$(BIN)/pytest --version
	@echo "✅ Local toolchain looks OK."

doctor-aws:
	@command -v aws >/dev/null && aws --version || (echo "AWS CLI not found" && exit 1)
	@command -v terraform >/dev/null && terraform -version || (echo "Terraform not found" && exit 1)
	@echo "✅ AWS toolchain looks OK."

# Terraform commands are routed through infra/terraform
# FIX: Ensure artifacts exist (pack-lambda) and tools are present (doctor-aws) before deploying.
deploy-dev: doctor-aws pack-lambda
	@cd infra/terraform && terraform init -upgrade && terraform apply -auto-approve

smoke-cloud:
	@$(MAKE) smoke-cloud-jwt

smoke-cloud-jwt:
	@cd $(ROOT) && $(PY) scripts/smoke_cloud_jwt.py

logs-cloud:
	@cd $(ROOT) && $(PY) scripts/logs_cloud.py

destroy-dev:
	@cd infra/terraform && terraform init && terraform destroy -auto-approve

# -----------------------------------------------------------------------------
# Docker (reviewer empathy)
# -----------------------------------------------------------------------------
docker-check:
	@command -v docker >/dev/null 2>&1 || (echo "❌ Docker not found. Install Docker Desktop / engine to use docker-* targets." && exit 1)

docker-build: docker-check
	@docker build -t ai-security-gateway:local .

docker-run: docker-check
	@docker run --rm -p 8000:8000 \
		-e AUTH_MODE=headers \
		-e ALLOW_INSECURE_HEADERS=true \
		ai-security-gateway:local

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
clean:
	rm -rf $(VENV) dist .pytest_cache .ruff_cache __pycache__
	find . -name "*.pyc" -delete
