#!/usr/bin/env python3
"""Create a clean, reproducible zip package for this skill."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


EXCLUDED_NAMES = {"__pycache__", ".DS_Store", "target", ".git"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def included(path: Path) -> bool:
    return not (
        any(part in EXCLUDED_NAMES for part in path.parts)
        or path.suffix in EXCLUDED_SUFFIXES
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    skill_dir = args.skill_dir.resolve()
    output = args.output.resolve()
    if not (skill_dir / "SKILL.md").is_file():
        raise SystemExit(f"missing SKILL.md in {skill_dir}")
    if not (skill_dir / "README.md").is_file():
        raise SystemExit(f"missing README.md in {skill_dir}")
    if output.parent == skill_dir or output == skill_dir:
        raise SystemExit("package output must be outside the skill directory")

    files = sorted(
        path for path in skill_dir.rglob("*")
        if path.is_file() and included(path.relative_to(skill_dir))
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    root_name = skill_dir.name
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, Path(root_name, path.relative_to(skill_dir)).as_posix())
    print(f"Packaged {len(files)} files: {output}")


if __name__ == "__main__":
    main()
