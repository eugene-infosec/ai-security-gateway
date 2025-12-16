#!/usr/bin/env python3
import subprocess
import sys
import os

# Extensions that should NEVER be committed
BLOCK_EXTENSIONS = {".zip", ".tfstate", ".tfplan", ".env", ".pyc"}
# Filenames that should NEVER be committed
BLOCK_FILES = {"lambda_function.zip", ".env", "terraform.tfvars", "override.tf"}


def main():
    # Get list of staged files
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        staged_files = result.stdout.splitlines()
    except subprocess.CalledProcessError:
        # Likely initial commit or empty repo issues; safe to pass if git fails
        return

    failures = []
    for filepath in staged_files:
        filename = os.path.basename(filepath)
        _, ext = os.path.splitext(filename)

        # Check strict blocklist
        if filename in BLOCK_FILES or ext in BLOCK_EXTENSIONS:
            failures.append(filepath)

        # Check for env files that might look like .env.production
        if filename.startswith(".env"):
            failures.append(filepath)

        # Check for terraform state backups like terraform.tfstate.backup
        if ".tfstate" in filename:
            failures.append(filepath)

    if failures:
        print("❌ CRITICAL: Attempting to commit blocked artifacts!")
        for f in failures:
            print(f"   - {f}")
        print(
            "\nThese files are strictly forbidden. Unstage them (git reset HEAD <file>) and update .gitignore."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
