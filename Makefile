.PHONY: doctor doctor-aws install run-local test gate ci deploy-dev destroy-dev package-lambda smoke-dev

# 1. SETUP & CHECKS
doctor:
	@echo "Checking local dependencies..."
	@which python3 > /dev/null || (echo "❌ Python3 missing" && exit 1)
	@which git > /dev/null || (echo "❌ Git missing" && exit 1)
	@echo "✅ Local tools found."

doctor-aws:
	@echo "Checking Cloud dependencies..."
	@which terraform > /dev/null || (echo "❌ Terraform missing" && exit 1)
	@which aws > /dev/null || (echo "❌ AWS CLI missing" && exit 1)
	@aws configure list >/dev/null 2>&1 || true # Senior proof: Check config without leaking
	@echo "✅ Cloud tools found."
	@echo "Checking AWS Identity..."
	@aws sts get-caller-identity --query "Arn" --output text || (echo "❌ AWS Auth failed" && exit 1)
	@echo "✅ AWS Identity confirmed."

# 2. LOCAL DEVELOPMENT
install:
	# Use python3 -m pip to match package-lambda consistency
	python3 -m pip install -r requirements.txt

run-local:
	@echo "Starting local API..."
	uvicorn app.main:app --reload --port 8000

# 3. TESTING & GATES
test:
	python3 -m pytest -q

gate:
	@echo "🔒 Running Security Gates..."
	PYTHONPATH=. python3 evals/no_admin_leakage_gate.py
	PYTHONPATH=. python3 evals/tenant_isolation_gate.py
	PYTHONPATH=. python3 evals/safe_logging_gate.py
	@echo "✨ ALL SECURITY GATES PASSED."

ci: test gate
	@echo "✅ CI Pipeline Verified."

# 4. INFRASTRUCTURE & DEPLOYMENT
package-lambda:
	@echo "📦 Packaging Lambda..."
	@which zip >/dev/null || (echo "❌ 'zip' missing (install it)"; exit 1)
	rm -rf build lambda_function.zip
	mkdir -p build
	# Use --upgrade to ensure no stale cache issues
	python3 -m pip install -r requirements.txt -t build --upgrade
	cp -r app build/
	# Exclude junk to keep zip clean
	cd build && zip -r ../lambda_function.zip . -x "*__pycache__*" "*.dist-info/*RECORD*"
	@echo "✅ Lambda package ready: lambda_function.zip"

deploy-dev: package-lambda
	@echo "🚀 Deploying to AWS (Dev)..."
	cd infra/terraform && terraform init && terraform apply -auto-approve

destroy-dev:
	@echo "💥 Destroying AWS resources..."
	cd infra/terraform && terraform destroy -auto-approve

smoke-dev:
	@echo "☁️ Running Smoke Test..."
	$(eval API_URL := $(shell cd infra/terraform && terraform output -raw base_url))
	@echo "Target: $(API_URL)"
	# 1. Liveness Check
	@curl -s "$(API_URL)/health" | grep "ok" && echo "✅ /health passed" || (echo "❌ /health failed" && exit 1)
	# 2. Identity Check (Fail if broken)
	@curl -s "$(API_URL)/whoami" -H "X-User: test" -H "X-Tenant: t1" -H "X-Role: intern" | grep "test" \
	  && echo "✅ /whoami passed" || (echo "❌ /whoami failed" && exit 1)
	# 3. Security Proof (Deny Receipt)
	@echo "▶ Triggering deny receipt (403)..."
	@curl -s -o /dev/null -w "%{http_code}\n" -X POST "$(API_URL)/ingest" \
	  -H 'Content-Type: application/json' \
	  -H 'X-User: malicious_intern' -H 'X-Tenant: tenant-a' -H 'X-Role: intern' \
	  -d '{"title":"HACK","body":"x","classification":"admin"}' | grep 403 && echo "✅ 403 triggered"
	@echo "Audit: Check CloudWatch logs for event=access_denied"

.PHONY: clean clean-tf

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf build dist lambda_function.zip

clean-tf:
	rm -rf infra/terraform/.terraform
	rm -f infra/terraform/terraform.tfstate infra/terraform/terraform.tfstate.backup infra/terraform/.terraform.tfstate.lock.info
	rm -f terraform.tfstate terraform.tfstate.backup .terraform.tfstate.lock.info