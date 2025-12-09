.PHONY: doctor run-local test gate ci deploy-dev destroy-dev

# 1. SETUP & CHECKS
doctor:
	@echo "Checking system dependencies..."
	@which python3 > /dev/null || (echo "❌ Python3 missing" && exit 1)
	@which git > /dev/null || (echo "❌ Git missing" && exit 1)
	@which terraform > /dev/null || (echo "❌ Terraform missing" && exit 1)
	@which aws > /dev/null || (echo "❌ AWS CLI missing" && exit 1)
	@echo "✅ Tools found."
	@echo "Checking AWS Identity..."
	@aws sts get-caller-identity --query "Arn" --output text || (echo "❌ AWS Auth failed" && exit 1)
	@echo "✅ AWS Identity confirmed."

# 2. LOCAL DEVELOPMENT
install:
	pip install -r requirements.txt

run-local:
	@echo "Starting local API..."
	uvicorn app.main:app --reload --port 8000

# 3. TESTING & GATES (The Hiring Signals)
test:
	# Quiet mode for cleaner CI logs
	python3 -m pytest -q

gate:
	@echo "🔒 Running Security Gates..."
	PYTHONPATH=. python3 evals/no_admin_leakage_gate.py
	PYTHONPATH=. python3 evals/tenant_isolation_gate.py
	PYTHONPATH=. python3 evals/safe_logging_gate.py
	@echo "✨ ALL SECURITY GATES PASSED."

ci: test gate
	@echo "✅ CI Pipeline Verified."

# 4. INFRASTRUCTURE (Cost Safety)
deploy-dev:
	@echo "🚀 Deploying to AWS (Dev)..."
	cd infra/terraform && terraform init && terraform apply -auto-approve

destroy-dev:
	@echo "💥 Destroying AWS (Dev)..."
	cd infra/terraform && terraform destroy -auto-approve