#!/usr/bin/env python3
# Test DotSlash wrappers changed in a pull request.

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


# Read required environment variables or exit.
def require_env(*names: str) -> dict[str, str]:
    values = {}
    missing = []
    for name in names:
        value = os.environ.get(name)
        if not value:
            missing.append(name)
        else:
            values[name] = value
    if missing:
        raise SystemExit(
            "missing required environment variables: " + ", ".join(missing)
        )
    return values


# Run a command, optionally capturing stdout.
def run(
    args: list[str],
    /,
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(args), flush=True)
    return subprocess.run(
        args,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )


SMOKE_BINARY = "packages/python-build-standalone/bin/python3"


# List added or modified paths between two commits.
def git_changed(base_sha: str, head_sha: str, /, *paths: str) -> list[str]:
    result = run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            base_sha,
            head_sha,
            "--",
            *paths,
        ],
        check=True,
        capture=True,
    )
    return [line for line in result.stdout.splitlines() if line]


# Choose wrappers to test, including python3 when CI files change.
def binaries_to_test(base_sha: str, head_sha: str, /) -> list[str]:
    files = git_changed(base_sha, head_sha, "packages/*/bin/*")
    if git_changed(base_sha, head_sha, ".github"):
        print(f".github changed; also testing {SMOKE_BINARY}")
        if SMOKE_BINARY not in files:
            files.append(SMOKE_BINARY)
    return files


# Return whether the wrapper has an entry for this platform.
def has_platform(dotslash: str, file: str, platform: str, /) -> bool:
    parsed = run([dotslash, "--", "parse", file], check=True, capture=True)
    data = json.loads(parsed.stdout)
    return platform in data.get("platforms", {})


# Run the wrapper with --version, version, or --help.
# Windows has no shebang, so the wrapper must be invoked via dotslash.
def probe(dotslash: str, file: str, /) -> bool:
    prefix = [dotslash] if sys.platform == "win32" else []
    for args in (["--version"], ["version"], ["--help"]):
        result = run([*prefix, file, *args], check=False)
        if result.returncode == 0:
            return True
    return False


# Find the dotslash executable on PATH.
def find_dotslash() -> str:
    found = shutil.which("dotslash") or shutil.which("dotslash.exe")
    if not found:
        raise SystemExit("dotslash is not on PATH")
    return found


# Fetch and run each selected wrapper on this runner's platform.
def main() -> int:
    env = require_env("DOTSLASH_PLATFORM", "BASE_SHA", "HEAD_SHA")
    platform = env["DOTSLASH_PLATFORM"]
    dotslash = find_dotslash()

    files = binaries_to_test(env["BASE_SHA"], env["HEAD_SHA"])
    if not files:
        print("No package binaries or .github changes; skipping.")
        return 0

    print("Changed binaries:")
    for file in files:
        print(f"  {file}")

    failed = 0
    for file in files:
        print(f"\n== {file} ({platform}) ==", flush=True)
        if not Path(file).is_file():
            print(f"missing after checkout: {file}", file=sys.stderr)
            failed += 1
            continue
        if not has_platform(dotslash, file, platform):
            print(f"no {platform} entry; skipping")
            continue
        print("fetch")
        run([dotslash, "--", "fetch", file], check=True)
        print("run")
        if not probe(dotslash, file):
            print(f"failed to run {file}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
