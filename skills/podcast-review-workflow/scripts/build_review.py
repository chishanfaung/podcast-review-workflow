#!/usr/bin/env python3
"""Build a configured, non-destructive podcast review page."""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "assets" / "review-template"
VIEWS = {"left", "right", "split"}


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def media_duration(source: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(source)],
        check=True, capture_output=True, text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def inside_url(path: Path, root: Path) -> str:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"{path} must be inside --serve-root {root}") from error
    return "/" + "/".join(quote(part) for part in relative.parts)


def validate(words: dict, plan: dict, analysis: dict, duration: float) -> None:
    segments = words.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("words JSON needs a non-empty segments array")
    previous = -1.0
    for index, segment in enumerate(segments):
        text = segment.get("text")
        start, end = segment.get("start"), segment.get("end")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"segment {index} has empty text")
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in (start, end)):
            raise ValueError(f"segment {index} has invalid time")
        if start < previous - 0.05 or start < 0 or end <= start or end > duration + 0.1:
            raise ValueError(f"segment {index} is out of order or outside the source")
        previous = start

    if plan.get("cuts") or plan.get("preserve_all_content") is False:
        raise ValueError("this skill rejects cut plans; cuts must be [] and all content must be preserved")
    shots = plan.get("preview_shots")
    if not isinstance(shots, list) or not shots or shots[0].get("source_time") != 0:
        raise ValueError("preview_shots must start at 0 seconds")
    previous = -1.0
    for shot in shots:
        start = shot.get("source_time")
        if not isinstance(start, (int, float)) or not math.isfinite(start):
            raise ValueError("shot time must be finite")
        if start <= previous or start < 0 or start >= duration or shot.get("view") not in VIEWS:
            raise ValueError("shot times/types are invalid")
        previous = start

    analysis_duration = analysis.get("duration")
    if not isinstance(analysis_duration, (int, float)) or abs(analysis_duration - duration) > 0.1:
        raise ValueError("analysis duration does not match the source")
    samples = analysis.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValueError("analysis JSON needs samples")
    if any(sample.get("side") not in VIEWS for sample in samples):
        raise ValueError("analysis contains an invalid side")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--words", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--title", default="播客定剪版审片")
    parser.add_argument("--id", dest="review_id")
    parser.add_argument("--left-name", default="左侧嘉宾")
    parser.add_argument("--right-name", default="右侧嘉宾")
    parser.add_argument("--review-check", action="append", type=int, default=[])
    args = parser.parse_args()

    root, output = args.serve_root.resolve(), args.output.resolve()
    source, words_path = args.source.resolve(), args.words.resolve()
    plan_path, analysis_path = args.plan.resolve(), args.analysis.resolve()
    for path in (root, source, words_path, plan_path, analysis_path):
        if not path.exists():
            raise FileNotFoundError(path)
    try:
        output.relative_to(root)
    except ValueError as error:
        raise ValueError("--output must be inside --serve-root") from error

    duration = media_duration(source)
    words, plan, analysis = load(words_path), load(plan_path), load(analysis_path)
    validate(words, plan, analysis, duration)
    if "source_duration" in plan and abs(float(plan["source_duration"]) - duration) > 0.1:
        raise ValueError("plan duration does not match the source")
    review_id = args.review_id or re.sub(r"[^a-z0-9]+", "-", source.stem.lower()).strip("-") or "podcast"
    config = {
        "id": review_id,
        "title": args.title,
        "sourceName": source.name,
        "duration": duration,
        "videoUrl": inside_url(source, root),
        "wordsUrl": inside_url(words_path, root),
        "planUrl": inside_url(plan_path, root),
        "analysisUrl": inside_url(analysis_path, root),
        "sampleInterval": float(analysis.get("sample_interval", 0.5)),
        "names": {"left": args.left_name, "right": args.right_name, "split": "对话"},
        "reviewChecks": args.review_check,
    }
    output.mkdir(parents=True, exist_ok=True)
    page = (TEMPLATE / "index.html").read_text(encoding="utf-8").replace("{{TITLE}}", html.escape(args.title))
    (output / "index.html").write_text(page, encoding="utf-8")
    shutil.copy2(TEMPLATE / "style.css", output / "style.css")
    shutil.copy2(TEMPLATE / "formats.css", output / "formats.css")
    shutil.copy2(TEMPLATE / "app.js", output / "app.js")
    payload = "window.PODCAST_REVIEW_CONFIG = " + json.dumps(config, ensure_ascii=False, indent=2) + ";\n"
    (output / "review-config.js").write_text(payload, encoding="utf-8")
    print(f"Built: {output / 'index.html'}")
    print(f"Open after serving: /{output.relative_to(root).as_posix()}/")
    print("Boundary: cuts remain empty; character timing is playback highlighting only.")


if __name__ == "__main__":
    main()
