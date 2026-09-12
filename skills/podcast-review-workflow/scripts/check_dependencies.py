#!/usr/bin/env python3
"""Check dependencies for a specific podcast review workflow mode."""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys


ASR_MODULES = ("faster_whisper", "whisper", "mlx_whisper")
ASR_COMMANDS = ("whisper-cli", "whisper-cpp")


def present_command(name: str) -> str | None:
    return shutil.which(name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("existing-review", "build-review", "transcribe", "render"),
        required=True,
        help="the stage you intend to run",
    )
    args = parser.parse_args()

    checks: list[tuple[str, bool, str]] = [("python3", sys.version_info >= (3, 10), sys.executable)]
    if args.mode in {"build-review", "transcribe", "render"}:
        checks.append(("ffprobe", present_command("ffprobe") is not None, present_command("ffprobe") or "missing"))
    if args.mode in {"transcribe", "render"}:
        checks.append(("ffmpeg", present_command("ffmpeg") is not None, present_command("ffmpeg") or "missing"))
    if args.mode == "transcribe":
        modules = [name for name in ASR_MODULES if importlib.util.find_spec(name)]
        commands = [name for name in ASR_COMMANDS if present_command(name)]
        detail = ", ".join(modules + commands) if modules or commands else "no supported module/command detected"
        checks.append(("ASR backend", bool(modules or commands), detail))

    print(f"mode: {args.mode}")
    for name, ok, detail in checks:
        print(f"{'OK  ' if ok else 'MISS'} {name}: {detail}")
    if args.mode == "existing-review":
        print("NOTE browser availability and source codec still require manual verification")
    if not all(ok for _, ok, _ in checks):
        print("STOP missing required dependency; do not claim this mode completed", file=sys.stderr)
        raise SystemExit(1)
    print("READY dependency probe passed; continue with the README compatibility gate")


if __name__ == "__main__":
    main()
