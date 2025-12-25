#!/usr/bin/env python3
"""Build dist/lambda.zip for AWS Lambda.

Goal: a reviewer can run `make deploy-dev` from a clean machine and succeed.

We vendor *runtime* dependencies into the zip so the Lambda can import FastAPI /
Mangum / Pydantic, etc.

Important: We target the Lambda runtime environment (Linux x86_64, CPython 3.12)
by downloading wheels and unpacking them ourselves. This works even if the
developer is on Windows/macOS or a different Python version locally.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = DIST_DIR / "lambda_build"
WHEELS_DIR = DIST_DIR / "wheels"
OUTPUT_ZIP = DIST_DIR / "lambda.zip"

RUNTIME_REQ = ROOT_DIR / "requirements-runtime.txt"
APP_DIR = ROOT_DIR / "app"

# AWS Lambda Python 3.12 uses Amazon Linux 2023 (glibc based)
TARGET_PLATFORM = "manylinux2014_x86_64"
TARGET_IMPLEMENTATION = "cp"
TARGET_PYTHON_VERSION = "312"
TARGET_ABI = "cp312"


def _pip_download_runtime_wheels(wheels_dir: Path) -> None:
    if not RUNTIME_REQ.exists():
        raise FileNotFoundError(f"Missing {RUNTIME_REQ}")

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--no-cache-dir",
        "-r",
        str(RUNTIME_REQ),
        "-d",
        str(wheels_dir),
        "--platform",
        TARGET_PLATFORM,
        "--implementation",
        TARGET_IMPLEMENTATION,
        "--python-version",
        TARGET_PYTHON_VERSION,
        "--abi",
        TARGET_ABI,
        "--only-binary",
        ":all:",
    ]

    print("📥 Downloading runtime wheels (Target: Linux x86_64)...")
    subprocess.check_call(cmd, cwd=str(ROOT_DIR))


def _unpack_wheels(wheels_dir: Path, target_dir: Path) -> None:
    whls = sorted(wheels_dir.glob("*.whl"))
    if not whls:
        raise RuntimeError(f"No wheels downloaded into {wheels_dir}")

    print(f"📦 Unpacking {len(whls)} wheels...")
    for whl in whls:
        with zipfile.ZipFile(whl, "r") as zf:
            zf.extractall(target_dir)


def _copy_app(target_dir: Path) -> None:
    if not APP_DIR.exists():
        raise FileNotFoundError(f"Missing {APP_DIR}")

    dest = target_dir / "app"

    def _ignore(_dir: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for n in names:
            if n == "__pycache__" or n.endswith(".pyc"):
                ignored.add(n)
        return ignored

    shutil.copytree(APP_DIR, dest, dirs_exist_ok=True, ignore=_ignore)


def _zip_dir(source_dir: Path, out_zip: Path) -> None:
    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in source_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if "__pycache__" in file_path.parts or file_path.suffix == ".pyc":
                continue
            arcname = file_path.relative_to(source_dir)
            zf.write(file_path, arcname)


def main() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    WHEELS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"📦 Building Lambda artifact -> {OUTPUT_ZIP}")

    _pip_download_runtime_wheels(WHEELS_DIR)
    _unpack_wheels(WHEELS_DIR, BUILD_DIR)
    _copy_app(BUILD_DIR)

    _zip_dir(BUILD_DIR, OUTPUT_ZIP)

    size_kb = int(os.path.getsize(OUTPUT_ZIP) / 1024)
    print(f"✅ Done. lambda.zip size ≈ {size_kb} KB")


if __name__ == "__main__":
    main()
