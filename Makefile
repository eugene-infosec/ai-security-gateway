.PHONY: install doctor doctor-aws fmt lint sec test gate tf-check preflight clean package-lambda deploy-dev destroy-dev smoke-dev logs-cloud run-local

# 1. SETUP & CHECKS
doctor:
	@echo "🏥 Checking Local Environment..."
	@which python3 > /dev/null || (echo "❌ Python3 missing" && exit 1)
	@which git > /dev/null || (echo "❌ Git missing" && exit 1)
	@echo "✅ Tools found."

doctor-aws:
	@echo "☁️ Checking AWS Environment..."
	@which terraform >/dev/null || (echo "❌ terraform missing" && exit 1)
	@which aws >/dev/null || (echo "❌ aws cli missing" && exit 1)
	@aws sts get-caller-identity --query "Arn" --output text >/dev/null || (echo "❌ AWS auth failed" && exit 1)
	@echo "✅ AWS identity confirmed"

install:
	@echo "📦 Installing dependencies..."
	.venv/bin/pip install -r requirements-runtime.txt
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
	@if [ -d "app" ]; then .venv/bin/bandit -q -r app; fi
	.venv/bin/pip-audit

tf-check:
	@echo "☁️ Terraform fmt/validate"
	terraform -chdir=infra/terraform fmt -check -recursive
	terraform -chdir=infra/terraform init -backend=false >/dev/null
	@if [ -f dist/lambda.zip ]; then \
		terraform -chdir=infra/terraform validate ; \
	else \
		echo "⚠️ dist/lambda.zip missing (run: make package-lambda). Skipping terraform validate." ; \
	fi

tf-validate: package-lambda
	@echo "☁️ Terraform validate (requires lambda.zip)"
	terraform -chdir=infra/terraform init -backend=false >/dev/null
	terraform -chdir=infra/terraform validate

# 3. TESTING & GATES
test:
	@echo "🧪 Running Unit Tests..."
	# FIX: Add PYTHONPATH=. so pytest can find 'app'
	PYTHONPATH=. .venv/bin/pytest -q

gate:
	@echo "🔒 Running Security Gates..."
	PYTHONPATH=. .venv/bin/python3 evals/no_admin_leakage_gate.py
	PYTHONPATH=. .venv/bin/python3 evals/tenant_isolation_gate.py
	PYTHONPATH=. .venv/bin/python3 evals/safe_logging_gate.py
	@echo "✨ ALL SECURITY GATES PASSED."

preflight: fmt lint sec test gate
	@echo "🚀 READY FOR COMMIT."

# 4. DEPLOYMENT & CLOUD
package-lambda:
	@echo "📦 Packaging Lambda -> dist/lambda.zip"
	@which zip >/dev/null || (echo "❌ 'zip' missing (sudo apt-get install zip)" && exit 1)
	rm -rf dist/.build dist/lambda.zip
	mkdir -p dist/.build
	.venv/bin/python3 -m pip install -r requirements-runtime.txt -t dist/.build --upgrade
	cp -r app dist/.build/
	cd dist/.build && zip -r ../lambda.zip . -x "*__pycache__*" "*.dist-info/*RECORD*"
	@echo "✅ Built dist/lambda.zip"

deploy-dev: package-lambda
	@echo "🚀 Deploying (dev)"
	terraform -chdir=infra/terraform init
	terraform -chdir=infra/terraform apply -auto-approve

destroy-dev:
	@echo "💥 Destroying (dev)"
	terraform -chdir=infra/terraform destroy -auto-approve

smoke-dev:
	@echo "☁️ Smoke test (dev)"
	$(eval API_URL := $(shell terraform -chdir=infra/terraform output -raw base_url))
	@echo "Target: $(API_URL)"
	# 1. Liveness
	@curl -s "$(API_URL)/health" | grep "ok" && echo "✅ /health passed" || (echo "❌ /health failed" && exit 1)
	# 2. Identity Check
	@curl -s "$(API_URL)/whoami" -H "X-User: test" -H "X-Tenant: tenant-a" -H "X-Role: intern" | grep "tenant-a" \
	  && echo "✅ /whoami passed" || (echo "❌ /whoami failed" && exit 1)
	# 3. Security Proof (Deny Receipt)
	@echo "▶ Triggering deny receipt (expect 403)..."
	@curl -s -o /dev/null -w "%{http_code}\n" -X POST "$(API_URL)/ingest" \
	  -H 'Content-Type: application/json' \
	  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
	  -d '{"title":"HACK","body":"x","classification":"admin"}' | grep 403 && echo "✅ 403 deny triggered" || (echo "❌ expected 403" && exit 1)

logs-cloud:
	@echo "Logs (last 10m): /aws/lambda/ai-security-gateway-dev"
	aws logs tail /aws/lambda/ai-security-gateway-dev --follow --since 10m

run-local:
	@echo "🚀 Starting Local API..."
	.venv/bin/uvicorn app.main:app --reload --port 8000

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist build
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
