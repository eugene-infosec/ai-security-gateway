#!/usr/bin/env python3
import subprocess
import os


def main():
    cwd = os.path.join(os.path.dirname(__file__), "../infra/terraform")
    group = subprocess.run(
        ["terraform", "output", "-raw", "lambda_log_group"],
        cwd=cwd,
        capture_output=True,
        text=True,
    ).stdout.strip()
    print(f"🔍 Tailing: {group}")
    try:
        subprocess.run(["aws", "logs", "tail", group, "--follow", "--format", "short"])
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
