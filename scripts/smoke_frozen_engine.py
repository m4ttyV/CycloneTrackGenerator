"""Validate a frozen CycloneEngine without database credentials or networking."""

import json
from pathlib import Path
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/smoke_frozen_engine.py path/to/CycloneEngine.exe", file=sys.stderr)
        return 2

    exe = Path(sys.argv[1]).resolve()
    if not exe.is_file():
        print(f"Executable not found: {exe}", file=sys.stderr)
        return 2

    # The build must work without a local confing.conf and without Python on PATH.
    result = subprocess.run(
        [str(exe)],
        cwd=str(exe.parent),
        input=json.dumps({"action": "self-test"}) + "\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )

    if result.returncode != 0:
        print(f"Engine exited with {result.returncode}", file=sys.stderr)
        print("STDOUT:\n" + result.stdout[-4000:], file=sys.stderr)
        print("STDERR:\n" + result.stderr[-8000:], file=sys.stderr)
        return 1

    try:
        response = json.loads(result.stdout.strip())
        if response.get("ok") is not True:
            raise ValueError(f"Unexpected response: {response}")
        if response["data"]["status"] != "ok" or response["data"]["rendered_png_bytes"] <= 100:
            raise ValueError(f"Invalid self-test result: {response}")
    except (ValueError, KeyError, TypeError) as exc:
        print("Engine produced invalid JSON / invalid PNG result", file=sys.stderr)
        print(result.stdout[-4000:], file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(
        f"PASS: CycloneEngine self-test rendered "
        f"{response['data']['rendered_png_bytes']} bytes of PNG."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
