#!/usr/bin/env python3
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
DIST_DIR = ROOT_DIR / "dist"
SOURCE_DIR = ROOT_DIR / "app"
OUTPUT_ZIP = DIST_DIR / "lambda.zip"


def main():
    if not DIST_DIR.exists():
        DIST_DIR.mkdir()

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    print(f"📦 Packaging {SOURCE_DIR} -> {OUTPUT_ZIP}")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in SOURCE_DIR.rglob("*"):
            if (
                file_path.is_file()
                and "__pycache__" not in file_path.parts
                and file_path.suffix != ".pyc"
            ):
                arcname = file_path.relative_to(ROOT_DIR)
                zf.write(file_path, arcname)
    print("✅ Build complete.")


if __name__ == "__main__":
    main()
