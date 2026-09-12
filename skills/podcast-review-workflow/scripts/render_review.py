#!/usr/bin/env python3
"""Render horizontal or vertical video from reviewed shots/text.

The normal mode preserves the source timeline.  ``--apply-skips`` is an
explicit sentence-level finishing step: it removes whole Whisper segments
marked by the review page, never character ranges.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def load(path: Path | None, default: dict) -> dict:
    if path is None: return default
    return json.loads(path.read_text(encoding="utf-8"))


def clock(seconds: float) -> str:
    value = round(seconds * 100)
    hours, value = divmod(value, 360000)
    minutes, value = divmod(value, 6000)
    whole, fraction = divmod(value, 100)
    return f"{hours}:{minutes:02}:{whole:02}.{fraction:02}"


def ass_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", "（").replace("}", "）")


def mark_keywords(text: str, keywords: list[str], color: str = "&H004FD2FF&", base_color: str = "&H00FFFFFF&") -> str:
    marks = [False] * len(text)
    for keyword in keywords:
        start = 0
        while keyword and (found := text.find(keyword, start)) >= 0:
            for index in range(found, found + len(keyword)): marks[index] = True
            start = found + len(keyword)
    result, active = [], False
    for index, char in enumerate(text):
        if marks[index] != active:
            result.append(r"{\c" + (color if marks[index] else base_color) + "}")
            active = marks[index]
        result.append(ass_escape(char))
    if active: result.append(r"{\c" + base_color + "}")
    return "".join(result)


def wrap_ass(text: str, width: int) -> str:
    # ASS tags do not count toward line width.
    visible, output, count = False, [], 0
    index = 0
    while index < len(text):
        if text[index] == "{":
            end = text.find("}", index)
            if end >= 0:
                output.append(text[index:end + 1]); index = end + 1; continue
        if count and count % width == 0: output.append(r"\N")
        output.append(text[index]); count += 1; index += 1
    return "".join(output)


def enabled_expression(shots: list[dict], view: str, duration: float) -> str:
    ranges = []
    for index, shot in enumerate(shots):
        end = shots[index + 1]["source_time"] if index + 1 < len(shots) else duration
        if shot["view"] == view:
            ranges.append(f"gte(t,{shot['source_time']})*lt(t,{end})")
    return "+".join(ranges) or "0"


def normalize_chapters(raw: list[dict] | dict, duration: float) -> list[dict]:
    """Normalize optional in-video chapter labels while preserving source time."""
    if isinstance(raw, dict):
        raw = raw.get("chapters", [])
    chapters = []
    for item in raw or []:
        try:
            start = max(0.0, min(duration, float(item["start"])))
        except (KeyError, TypeError, ValueError):
            continue
        label = str(item.get("label", "")).strip()
        if label:
            chapters.append({"start": start, "label": label})
    chapters.sort(key=lambda item: item["start"])
    deduped = []
    for chapter in chapters:
        if deduped and chapter["start"] <= deduped[-1]["start"]:
            deduped[-1] = chapter
        else:
            deduped.append(chapter)
    for index, chapter in enumerate(deduped):
        chapter["end"] = deduped[index + 1]["start"] if index + 1 < len(deduped) else duration
    return [chapter for chapter in deduped if chapter["end"] > chapter["start"]]


def skip_ranges(words: dict, settings: dict, duration: float) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """Return removed and kept source ranges from complete segment skips."""
    removed = []
    segments = words.get("segments", [])
    for raw_index in settings.get("skipSegments", []) if settings else []:
        try:
            segment = segments[int(raw_index)]
            start = max(0.0, min(duration, float(segment["start"])))
            end = max(0.0, min(duration, float(segment["end"])))
        except (IndexError, KeyError, TypeError, ValueError):
            continue
        if end > start:
            removed.append((start, end))
    removed.sort()
    merged = []
    for start, end in removed:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    kept, cursor = [], 0.0
    for start, end in merged:
        if start > cursor:
            kept.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < duration:
        kept.append((cursor, duration))
    return merged, kept


def build_ass(words: dict, plan: dict, settings: dict, duration: float, fmt: str, output: Path, chapters: list[dict] | None = None) -> None:
    edits, emphases = settings.get("edits", {}), settings.get("emphases", {})
    disabled = set(settings.get("disabledQuotes", []))
    quotes = [quote for quote in plan.get("quotes", []) if quote.get("id") not in disabled]
    vertical = fmt == "vertical"
    resolution = (1080, 1920) if vertical else (1920, 1080)
    # The horizontal chapter strip occupies the bottom 12% of the frame, so
    # move subtitles above it only when that strip is being rendered.
    font, margin, width = (74, 160, 10) if vertical else (48, 190 if chapters else 60, 23)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {resolution[0]}
PlayResY: {resolution[1]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Normal,Heiti SC,{font},&H00FFFFFF,&H00FFFFFF,&H00101010,&H70000000,0,0,0,0,100,100,1,0,1,4,1,2,70,70,{margin},1
Style: Quote,Heiti SC,{round(font*1.08)},&H008BE2FF,&H008BE2FF,&H00101010,&H70000000,-1,0,0,0,100,100,1,0,1,4,1,2,70,70,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for index, segment in enumerate(words["segments"]):
        start, end = max(0.0, float(segment["start"])), min(duration, float(segment["end"]))
        if end <= start: continue
        text = str(edits.get(str(index), segment["text"])).strip()
        if not text: continue
        is_quote = any(quote["start"] < end and quote["end"] > start for quote in quotes)
        # Keep subtitles at two lines. Long cues are paged across their existing
        # time span; this changes display timing only and never creates a cut.
        page_size = width * 2
        pages = [text[offset:offset + page_size] for offset in range(0, len(text), page_size)]
        for page_index, page in enumerate(pages):
            page_start = start + (end - start) * page_index / len(pages)
            page_end = start + (end - start) * (page_index + 1) / len(pages)
            page_keywords = [keyword for keyword in emphases.get(str(index), []) if keyword in page]
            styled = mark_keywords(page, page_keywords, base_color="&H008BE2FF&" if is_quote else "&H00FFFFFF&")
            events.append(f"Dialogue: 0,{clock(page_start)},{clock(page_end)},{'Quote' if is_quote else 'Normal'},,0,0,0,,{wrap_ass(styled,width)}")
    output.write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def ffmpeg_text(text: str) -> str:
    return str(text).replace("\\", r"\\").replace(":", r"\:").replace("'", r"\'").replace("%", r"\%")


def chapter_overlay_graph(input_label: str, chapters: list[dict], output_label: str, width: int = 1920, height: int = 1080) -> str:
    """Draw a static chapter strip with a time-aware gray active block."""
    if not chapters:
        return f"[{input_label}]format=yuv420p[{output_label}]"
    bar_height = round(height * 0.12)
    bar_top = height - bar_height
    min_seconds = 220.0
    weights = [max(min_seconds, chapter["end"] - chapter["start"]) for chapter in chapters]
    total = sum(weights)
    graph, current, cursor = [], input_label, 0.0
    for index, (chapter, weight) in enumerate(zip(chapters, weights)):
        x = round(width * cursor / total)
        next_x = width if index == len(chapters) - 1 else round(width * (cursor + weight) / total)
        box_width = max(1, next_x - x)
        base = f"chapter{index}"
        active = f"chapter{index}active"
        bordered = f"chapter{index}border"
        texted = f"chapter{index}text"
        # Match the HTML overlay: a dark, nearly uniform strip with only a
        # subtle alternating tint.  The active chapter is then unambiguous
        # when its gray fill is applied below.
        base_color = "0x15191d@0.94" if index % 2 == 0 else "0x1b2025@0.94"
        graph.append(f"[{current}]drawbox=x={x}:y={bar_top}:w={box_width}:h={bar_height}:color={base_color}:t=fill[{base}]")
        graph.append(f"[{base}]drawbox=x={x}:y={bar_top}:w={box_width}:h={bar_height}:color=0x767e87@0.92:t=fill:enable='between(t,{chapter['start']:.3f},{chapter['end']:.3f})'[{active}]")
        graph.append(f"[{active}]drawbox=x={x}:y={bar_top}:w={box_width}:h={bar_height}:color=0xe4e8eb@0.8:t=2:enable='between(t,{chapter['start']:.3f},{chapter['end']:.3f})'[{bordered}]")
        label = ffmpeg_text(chapter["label"])
        graph.append(
            f"[{bordered}]drawtext=fontfile='/System/Library/Fonts/STHeiti Medium.ttc':text='{label}':fontsize=26:fontcolor=white:borderw=2:bordercolor=black@0.82:x={x}+({box_width}-text_w)/2:y={bar_top}+({bar_height}-text_h)/2[{texted}]"
        )
        current, cursor = texted, cursor + weight
    graph.append(f"[{current}]format=yuv420p[{output_label}]")
    return "\n".join(line + (";" if index < len(graph) - 1 else "") for index, line in enumerate(graph))


def build_filter(shots: list[dict], duration: float, fmt: str, ass_path: Path, output: Path, chapters: list[dict] | None = None, kept_ranges: list[tuple[float, float]] | None = None) -> bool:
    left, right = enabled_expression(shots, "left", duration), enabled_expression(shots, "right", duration)
    escaped_ass = str(ass_path.resolve()).replace("'", r"\'")
    if fmt == "horizontal":
        graph = f"""[0:v]split=3[base][l][r];
[l]crop=iw/2:ih/2:0:ih/4,scale=1920:1080:flags=lanczos[left];
[r]crop=iw/2:ih/2:iw/2:ih/4,scale=1920:1080:flags=lanczos[right];
[base][left]overlay=0:0:enable='{left}'[vl];
[vl][right]overlay=0:0:enable='{right}',ass=filename='{escaped_ass}'[captioned]
        """
        if chapters:
            graph = graph.rstrip() + ";\n" + chapter_overlay_graph("captioned", chapters, "chaptered") + "\n"
        else:
            graph = graph.replace("[captioned]\n", "[captioned];\n[captioned]format=yuv420p[chaptered]\n")
    else:
        graph = f"""[0:v]split=4[l][r][ls][rs];
[l]crop=ih*9/32:ih/2:(iw/2-ih*9/32)/2:ih/4,scale=1080:1920:flags=lanczos[left];
[r]crop=ih*9/32:ih/2:iw/2+(iw/2-ih*9/32)/2:ih/4,scale=1080:1920:flags=lanczos[right];
[ls]crop=iw/2:ih/2:0:ih/4,scale=1080:608:flags=lanczos[leftwide];
[rs]crop=iw/2:ih/2:iw/2:ih/4,scale=1080:608:flags=lanczos[rightwide];
[leftwide][rightwide]vstack=inputs=2[stack];
[stack]pad=1080:1920:0:352:black[base];
[base][left]overlay=0:0:enable='{left}'[vl];
[vl][right]overlay=0:0:enable='{right}',ass=filename='{escaped_ass}',format=yuv420p[chaptered]
"""
    if kept_ranges and len(kept_ranges) > 0:
        count = len(kept_ranges)
        video_src = "".join(f"[vsrc{i}]" for i in range(count))
        audio_src = "".join(f"[asrc{i}]" for i in range(count))
        graph = graph.rstrip() + f";\n[chaptered]split={count}{video_src};\n[0:a:0]asplit={count}{audio_src};\n"
        concat_inputs = []
        for i, (start, end) in enumerate(kept_ranges):
            graph += f"[vsrc{i}]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[vkeep{i}];\n"
            graph += f"[asrc{i}]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[akeep{i}];\n"
            concat_inputs.extend((f"[vkeep{i}]", f"[akeep{i}]"))
        graph += "".join(concat_inputs) + f"concat=n={count}:v=1:a=1[vout][aout]\n"
        output.write_text(graph, encoding="utf-8")
        return True
    graph = graph.rstrip() + ";\n[chaptered]format=yuv420p[vout]\n"
    output.write_text(graph, encoding="utf-8")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--words", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--format", choices=("horizontal", "vertical"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chapters", type=Path, help="Optional JSON file with in-video chapter labels and source starts")
    parser.add_argument("--apply-skips", action="store_true", help="Remove complete short-sentence segments listed in review settings")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--sample-seconds", type=float)
    parser.add_argument("--encoder", default="libx264", help="Use h264_videotoolbox for faster macOS hardware encoding")
    args = parser.parse_args()
    words, plan, settings = load(args.words, {}), load(args.plan, {}), load(args.settings, {})
    if plan.get("cuts") or settings.get("cuts"): raise ValueError("cuts must be empty")
    duration = float(plan["source_duration"])
    if settings and (settings.get("source") != args.source.name or abs(settings.get("duration", -1) - duration) > 0.1): raise ValueError("settings do not match source")
    shots = settings.get("shotOverrides") or plan["preview_shots"]
    prefix = args.output.with_suffix("")
    ass_path, filter_path = Path(str(prefix) + f".{args.format}.ass"), Path(str(prefix) + f".{args.format}.filter.txt")
    chapter_path = args.chapters
    chapters = normalize_chapters(load(chapter_path, []), duration) if chapter_path else []
    build_ass(words, plan, settings, duration, args.format, ass_path, chapters)
    removed, kept = skip_ranges(words, settings, duration) if args.apply_skips else ([], [])
    has_cuts = build_filter(shots, duration, args.format, ass_path, filter_path, chapters, kept if removed else None)
    print(f"Prepared {ass_path} and {filter_path}")
    if args.apply_skips:
        print(f"Sentence skips: {len(removed)} ranges removed, output duration about {sum(end-start for start, end in kept):.2f}s")
    if args.prepare_only: return
    # FFmpeg 8 deprecates -filter_complex_script.  The slash-prefixed option
    # reads the graph from the following file without putting a large filter
    # expression on the command line.
    command = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-stats", "-n", "-i", str(args.source),
               "-/filter_complex", str(filter_path), "-map", "[vout]"]
    command += ["-map", "[aout]" if has_cuts else "0:a:0", "-c:v", args.encoder]
    if args.encoder == "libx264": command += ["-preset", "medium", "-crf", "20"]
    else: command += ["-b:v", "5M", "-allow_sw", "1"]
    command += ["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    if args.sample_seconds: command += ["-t", str(args.sample_seconds)]
    command.append(str(args.output))
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
