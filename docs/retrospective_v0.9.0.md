# Retrospective (v0.9.0) - The Platinum Build

> **Theme:** Removing "It works on my machine" and ensuring absolute cross-platform reproducibility without Docker.

This release focused on **reviewer empathy** and **build engineering**. While v0.8.0 hardened the application security, v0.9.0 hardens the *deployment process* to ensure a hiring manager can deploy the project from a fresh MacBook, Windows laptop, or CI runner with zero friction.

## 1) Build Strategy: The "Docker-Free" Compromise

**Issue:** Building Python Lambdas typically requires Docker to compile C-extensions (like `pydantic-core`) for Amazon Linux. However, requiring a reviewer to install/run Docker is a high friction barrier. Naive zipping (used in v0.8.0) fails immediately on Cloud because macOS/Windows wheels are incompatible with Lambda's Linux environment.

**Fix:** **Implemented a Native Wheel Vendoring Strategy.**
- We wrote a custom builder (`scripts/package_lambda.py`) that uses `pip download` to fetch specific **`manylinux2014_x86_64`** binary wheels, regardless of the host OS.
- We explicitly locked the Terraform Lambda architecture to `x86_64` to match these artifacts.
- **Result:** A production-compatible artifact is built deterministically on any machine without needing Docker.

## 2) IaC Correctness: The Duplicate Resource Bug

**Issue:** A copy-paste error in `infra/terraform/cognito.tf` left two definitions of the User Pool—one secure (immutable) and one insecure (mutable). This caused Terraform to crash on apply, blocking the "happy path" for reviewers.

**Fix:** **Cleaned and Locked the Infrastructure.**
- Removed the duplicate resource, keeping only the strict `mutable = false` definition.
- Added `outputs.tf` to expose the deployed Region, preventing "Region Mismatch" errors when running smoke tests (`scripts/smoke_cloud_jwt.py`).
- **Result:** `terraform apply` is now idempotent and robust.

## 3) Operational Friction: The "Fresh Clone" Guarantee

**Issue:** The `make deploy-dev` command assumed the Lambda zip already existed. A reviewer running the command on a fresh clone would see a confusing "file not found" error.

**Fix:** **Chained Make Targets.**
- `make deploy-dev` now explicitly depends on `pack-lambda` and `doctor-aws`.
- **Result:** One command (`make deploy-dev`) reliably takes a fresh machine from "source code" to "live cloud deployment" with no manual intermediate steps.

## 4) Documentation Integrity

**Issue:** The v0.8.0 changelog claimed `starlette` was removed, but it was still present as a transitive dependency of `fastapi`. This inaccuracy was a "poke holes" moment for detailed reviewers.

**Fix:** **Clarified Dependency Claims.**
- Updated documentation to accurately reflect that we *pinned* dependencies to safe versions and enforce this via `pip-audit`, rather than claiming removal of necessary transitive packages.

## 5) Known limitations (intentional)

- **InMemoryStore:** Remains the default for zero-cost reproducibility.
- **Lexical Search:** Remains the default for deterministic testing.
- **Manual Wheel Unpacking:** Our build script manually unpacks wheels. While robust for this project, a massive scale production app would likely revert to Docker for complex dependency trees (e.g., `numpy` + system libs). We accepted this tradeoff for "Reviewer Simplicity."
