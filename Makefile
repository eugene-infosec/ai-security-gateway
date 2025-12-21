.PHONY: install doctor doctor-aws fmt lint sec test gate tf-check preflight clean package-lambda deploy-dev destroy-dev smoke-cloud smoke-local ci run-local

# ==============================================================================
# 1. SETUP & CHECKS
# ==============================================================================
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

# ==============================================================================
# 2. HYGIENE & SECURITY
# ==============================================================================
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

# The Standard CI Entrypoint
ci: fmt lint sec test gate
	@echo "✅ CI Gates Passed"

# ==============================================================================
# 3. TESTING & GATES
# ==============================================================================
test:
	@echo "🧪 Running Unit Tests..."
	AUTH_MODE=headers ALLOW_INSECURE_HEADERS=true TABLE_NAME="" \
	PYTHONPATH=. .venv/bin/python3 -m pytest -q

gate:
	@echo "🔒 Running Security Gates..."
	AUTH_MODE=headers ALLOW_INSECURE_HEADERS=true TABLE_NAME="" \
	PYTHONPATH=. .venv/bin/python3 evals/no_admin_leakage_gate.py

	AUTH_MODE=headers ALLOW_INSECURE_HEADERS=true TABLE_NAME="" \
	PYTHONPATH=. .venv/bin/python3 evals/tenant_isolation_gate.py

	AUTH_MODE=headers ALLOW_INSECURE_HEADERS=true TABLE_NAME="" \
	PYTHONPATH=. .venv/bin/python3 evals/safe_logging_gate.py
	@echo "✨ ALL SECURITY GATES PASSED."

preflight: ci
	@echo "🚀 READY FOR COMMIT."

# ==============================================================================
# 4. LOCAL DEVELOPMENT
# ==============================================================================
run-local:
	@echo "⚠️  STARTING IN LOCAL/INSECURE MODE (Headers Allowed)"
	export AUTH_MODE=headers; \
	export ALLOW_INSECURE_HEADERS=true; \
	export TABLE_NAME=""; \
	.venv/bin/uvicorn app.main:app --reload --port 8000

smoke-local:
	@echo "🔥 Smoke Test (Local Headers)"
	@curl -s http://127.0.0.1:8000/health | grep "ok" && echo "✅ /health passed"
	@curl -s http://127.0.0.1:8000/whoami \
		-H 'X-User: demo' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' | grep "user_id" \
		&& echo "✅ /whoami passed"

# ==============================================================================
# 5. DEPLOYMENT & CLOUD
# ==============================================================================
package-lambda:
	@echo "📦 Packaging Lambda -> dist/lambda.zip"
	@which zip >/dev/null || (echo "❌ 'zip' missing" && exit 1)
	rm -rf dist/.build dist/lambda.zip
	mkdir -p dist/.build
	.venv/bin/python3 -m pip install -r requirements-runtime.txt -t dist/.build --upgrade
	cp -r app dist/.build/
	cd dist/.build && zip -r ../lambda.zip . -x "*__pycache__*" "*.dist-info/*RECORD*"
	@echo "✅ Built dist/lambda.zip"

tf-check:
	@echo "☁️ Terraform fmt/validate"
	terraform -chdir=infra/terraform fmt -check -recursive
	terraform -chdir=infra/terraform init -backend=false >/dev/null
	@if [ -f dist/lambda.zip ]; then \
		terraform -chdir=infra/terraform validate ; \
	else \
		echo "⚠️ dist/lambda.zip missing. Skipping validate." ; \
	fi

deploy-dev: package-lambda
	@echo "🚀 Deploying (dev)"
	terraform -chdir=infra/terraform init
	terraform -chdir=infra/terraform apply -auto-approve

destroy-dev:
	@echo "💥 Destroying (dev)"
	terraform -chdir=infra/terraform destroy -auto-approve

logs-cloud:
	@echo "Logs (last 10m): /aws/lambda/ai-security-gateway-dev"
	aws logs tail /aws/lambda/ai-security-gateway-dev --follow --since 10m

# ==============================================================================
# 6. CLOUD SMOKE TESTS (JWT)
# ==============================================================================
smoke-cloud:
	@echo "☁️ Smoke Test (JWT Mode - REAL)"
	@if [ -z "$$JWT_TOKEN" ]; then echo "❌ Set JWT_TOKEN first: source scripts/auth.sh"; exit 1; fi
	$(eval API_URL := $(shell terraform -chdir=infra/terraform output -raw base_url))
	@echo "Target: $(API_URL)"

	@echo "1) /health (public)"
	@curl -s "$(API_URL)/health" | grep "ok" && echo "✅ /health passed" || (echo "❌ /health failed"; exit 1)

	@echo "2) /whoami (JWT)"
	@curl -s "$(API_URL)/whoami" -H "Authorization: Bearer $$JWT_TOKEN" | grep "tenant_id" \
	  && echo "✅ /whoami passed" || (echo "❌ /whoami failed"; exit 1)

	@echo "3) Trigger deny (JWT, expect 403)"
	@curl -s -o /dev/null -w "%{http_code}\n" -X POST "$(API_URL)/ingest" \
	  -H 'Content-Type: application/json' \
	  -H "Authorization: Bearer $$JWT_TOKEN" \
	  -d '{"title":"HACK","body":"x","classification":"admin"}' | grep 403 \
	  && echo "✅ 403 deny triggered" || (echo "❌ expected 403"; exit 1)

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage dist build
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
