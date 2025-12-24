#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def get_tf_output(name):
    cwd = os.path.join(os.path.dirname(__file__), "../infra/terraform")
    return subprocess.run(
        ["terraform", "output", "-raw", name], cwd=cwd, capture_output=True, text=True
    ).stdout.strip()


def main():
    print("☁️  Running Cloud Smoke Test")
    base_url = get_tf_output("base_url")
    token = os.environ.get("JWT_TOKEN")

    if not base_url:
        print("❌ No URL")
        sys.exit(1)

    if not token:
        print("❌ No JWT_TOKEN. Run 'source scripts/auth.sh' first.")
        sys.exit(1)

    print(f"   Target: {base_url}")

    # WHOAMI Test
    req = Request(f"{base_url}/whoami", headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(req) as res:
            data = json.load(res)
            print(f"✅ /whoami: {res.status} - User: {data.get('user_id', 'unknown')}")
    except HTTPError as e:
        print(f"❌ /whoami failed: {e.code}")
        sys.exit(1)


if __name__ == "__main__":
    main()
