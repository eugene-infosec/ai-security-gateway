# ADR 0003: Native Cross-Platform Build Strategy (No Docker)

> Truth scope: accurate as of **v0.9.1**.

## Context

AWS Lambda requires Python dependencies (specifically compiled extensions like `pydantic-core`) to be compatible with Amazon Linux 2023 (`manylinux2014_x86_64`).

However, developers and reviewers often work on **macOS (ARM64)** or **Windows (x86_64)**. A naive `pip install -t dist/` on these machines produces artifacts that crash on Lambda with `ELF` binary format errors.

The industry standard solution is to build artifacts inside a Docker container (e.g., `sam build --use-container`). However, requiring Docker adds significant friction:
1.  **Dependency Weight:** Reviewers must install/start Docker Desktop.
2.  **Opacity:** The build process happens inside a black box.
3.  **CI Complexity:** CI pipelines need "Docker-in-Docker" or special runners.

## Decision

I implemented a **Pure Python Build Strategy** that runs natively on the host machine but targets the Lambda environment explicitly.

I use a custom build script (`scripts/package_lambda.py`) that:
1.  Uses `pip download` to fetch **binary wheels** specifically for `platform=manylinux2014_x86_64`, `python_version=312`, and `implementation=cp`.
2.  Unpacks these wheels into a staging directory.
3.  Copies application code on top.
4.  Zips the result.

## Consequences

### Positive
* **Zero-Friction Review:** A reviewer can run `make deploy-dev` on a fresh MacBook or Windows laptop without installing Docker.
* **Speed:** No container startup overhead; builds are limited only by network/disk speed.
* **Transparency:** The build logic is a readable Python script, not a Dockerfile abstraction.

### Negative
* **Maintenance:** I effectively re-implemented a partial package manager. I must ensure the script correctly handles wheel extraction.
* **Limitations:** This only works for Python dependencies. If I needed system-level libraries (e.g., `ffmpeg`), I would be forced to use Docker.

### Mitigation
* I explicitly locked the Terraform Lambda architecture to `x86_64` to match the wheels I download.
* I rely on `pip` to resolve dependency trees, only overriding the platform flags.
