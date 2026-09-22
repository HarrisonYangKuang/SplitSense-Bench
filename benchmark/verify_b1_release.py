#!/usr/bin/env python3
"""Verify the public Benchmark-B1 task inventory and frozen summary."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "TASK_MANIFEST.json").read_text())
summary = json.loads((ROOT / "reference_summary.json").read_text())
tasks = manifest["tasks"]
assert len(tasks) == 36
assert len({row["slug"] for row in tasks}) == 36
assert Counter(row["mode"] for row in tasks) == Counter({"direct": 12, "calculator": 12, "declarative": 12})
for row in tasks:
    path = ROOT.parent / row["source_file"]
    assert path.is_file(), path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row["source_sha256"], path
    if row["mode"] == "calculator":
        assert row["slug"].endswith("-v1r3")
    else:
        assert row["slug"].endswith("-v1r2")
assert summary["status"] == "PASS"
assert summary["native_runs"] == 36 and summary["sessions"] == 72
for mode in ("direct", "calculator", "declarative"):
    row = summary["mode_summaries"][mode]
    assert row["sessions"] == 24
    assert row["SA"] == row["EA"] == row["E2E"] == 1.0
print("PASS: 36 task sources and the 72-session B1 reference summary match the manifest")
