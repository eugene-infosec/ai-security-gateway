# ADR 0003: Native Cross-Platform Build Strategy (No Docker)

> Truth scope: accurate as of **v1.0.0**.

## Context

AWS Lambda requires Python dependencies (especially compiled extensions such as `pydantic-core`) to be compatible with the Lambda runtime OS/ABI (e.g., `manylinux2014_x86_64` for x86_64).

Developers and reviewers often work on:
- **macOS (ARM64)**
- **Windows (x86_64)**
- **Linux (various distros)**

A naive `pip install -t dist/` on the host machine can produce artifacts that crash on Lambda (e.g., `ELF` / binary format errors) because the installed wheels reflect the *host* platform, not Lambda.

The common solution is to build inside Docker (e.g., `sam build --use-container`). However, requiring Docker adds friction:

1. **Dependency weight:** reviewers must install and run Docker Desktop.
2. **Opacity:** build behavior is hidden behind container layers.
3. **CI complexity:** container builds often require special runners or Docker-in-Docker setup.

## Decision

Implement a **native, cross-platform packaging strategy** that runs on the host machine but targets Lambda explicitly.

A custom packaging script (`scripts/package_lambda.py`) performs a reproducible build by:

1. Using `pip download` to fetch **binary wheels** for the Lambda target platform:
   - `platform=manylinux2014_x86_64`
   - `python_version=3.12`
   - `implementation=cp`
2. Unpacking wheels into a staging directory.
3. Copying application code on top.
4. Zipping the resulting directory into the Lambda artifact.

This approach keeps the process readable and reproducible without requiring Docker.

## Consequences

### Positive

- **Zero-friction review:** a reviewer can run `make deploy-dev` on a fresh machine without installing Docker.
- **Fast iteration:** no container startup overhead; builds are bounded by network and disk.
- **Transparency:** build logic is explicit Python (easy to read, audit, and modify).
- **Consistency:** artifacts target the runtime platform regardless of the developer OS.

### Negative / Tradeoffs

- **Maintenance burden:** this re-implements part of what containerized build tools provide, and the script must correctly handle wheel acquisition and extraction.
- **Scope limitation:** this strategy targets **Python dependencies**. If system-level libraries are required (e.g., `ffmpeg`, native OS packages), Docker (or a Lambda layer / custom runtime) becomes the correct tool.

## Mitigations / Guardrails

- The Lambda architecture is pinned (e.g., `x86_64`) to match the target wheels downloaded by the script.
- Dependency resolution remains handled by `pip`; the script only overrides platform targeting flags.
- Packaging is exercised as part of the normal workflow (e.g., `make deploy-dev` depends on the packaging step), reducing the chance of drift.

## Notes

This ADR prioritizes **reviewer empathy** and **reproducibility**. The goal is a build that is production-shaped but still easy to validate on any laptop in a regulated-environment hiring loop.
