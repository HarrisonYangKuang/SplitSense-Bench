#!/usr/bin/env python3
"""Build or verify the deterministic public release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "RELEASE_MANIFEST.json"
EXCLUDED_PARTS = {".git", "__pycache__"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory() -> list[dict[str, object]]:
    files = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        files.append(
            {
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return files


def expected_manifest() -> dict[str, object]:
    files = inventory()
    return {
        "schema": "splitsense-public-release-manifest-v1",
        "release": "1.0.0",
        "release_date": "2026-09-21",
        "hash_algorithm": "SHA-256",
        "file_count": len(files),
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify without rewriting")
    args = parser.parse_args()
    expected = expected_manifest()
    if args.check:
        if not MANIFEST.is_file():
            print("FAIL: RELEASE_MANIFEST.json is missing")
            return 1
        actual = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if actual != expected:
            print("FAIL: release files do not match RELEASE_MANIFEST.json")
            return 1
        print(f"PASS: {expected['file_count']} public files match the release manifest")
        return 0
    MANIFEST.write_text(
        json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"WROTE: {expected['file_count']} public files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
