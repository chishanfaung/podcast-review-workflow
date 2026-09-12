#!/usr/bin/env python3
"""Validate a podcast review-settings JSON without changing it."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

VIEWS = {"left", "right", "split"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("settings", type=Path)
    parser.add_argument("--source")
    parser.add_argument("--duration", type=float)
    args = parser.parse_args()
    data = json.loads(args.settings.read_text(encoding="utf-8"))
    if data.get("version") != 1: raise ValueError("unsupported settings version")
    if args.source is not None and data.get("source") != args.source: raise ValueError("source mismatch")
    duration = args.duration if args.duration is not None else data.get("duration")
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0: raise ValueError("invalid duration")
    if args.duration is not None and abs(data.get("duration", -1) - args.duration) > 0.1: raise ValueError("duration mismatch")
    if data.get("cuts"): raise ValueError("cuts must be empty; character-level cutting is outside this skill")
    if not isinstance(data.get("edits", {}), dict): raise ValueError("edits must be an object")
    if not isinstance(data.get("emphases", {}), dict): raise ValueError("emphases must be an object")
    for key, values in data.get("emphases", {}).items():
        text = data.get("edits", {}).get(key)
        if not isinstance(values, list) or any(not isinstance(value, str) or not value or len(value) > 50 for value in values): raise ValueError("invalid emphasis values")
        if text is not None and any(value not in text for value in values): raise ValueError("emphasis is not present in edited text")
    if not isinstance(data.get("disabledQuotes", []), list): raise ValueError("disabledQuotes must be an array")
    for field in ("shotOverrides", "preview_shots"):
        shots = data.get(field)
        if shots is None: continue
        if not isinstance(shots, list) or not shots or shots[0].get("source_time") != 0: raise ValueError(f"{field} must start at 0")
        previous = -1.0
        for shot in shots:
            start = shot.get("source_time")
            if not isinstance(start, (int, float)) or not math.isfinite(start) or start <= previous or start < 0 or start >= duration: raise ValueError(f"invalid {field} time")
            if shot.get("view") not in VIEWS: raise ValueError(f"invalid {field} view")
            previous = start
    print(f"OK: {args.settings} is a non-destructive review-settings file")


if __name__ == "__main__":
    main()
