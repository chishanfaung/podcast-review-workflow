---
name: podcast-review-workflow
description: "Build or adapt a local podcast finishing workflow: inspect media, run local Whisper, preserve raw timing, correct obvious recognition errors, identify quote and keyword emphasis, derive a conservative speaker-camera plan, preview horizontal or vertical framing in HTML, export review settings, and optionally render 16:9 or 9:16 after review. Use for podcast transcription review, smart shot-switching, quote/keyword highlighting, social-video framing, or reusable review pages. Never use character-level timing to cut media."
---

# Podcast Review Workflow

Build a non-destructive review layer over the original podcast video. The browser is a decision tool, not an NLE. Before adapting the package, read [README.md](README.md) and run its compatibility gate; the bundled layout/render profile assumes a two-person, left/right split-screen recording unless the consumer adapts the geometry code as well.

## Hard boundaries

- Never create cuts from character-level timestamps. Character timings may drive playback highlighting only.
- Never auto-remove filler words, pauses, repeated words, or content unless the user separately asks for editorial suggestions.
- Keep `cuts` empty in every review-settings file. Reject imported settings whose `cuts` is non-empty.
- Do not reorder or transcode the source during review-page creation.
- Render horizontal or vertical output only after the user explicitly asks for output; rendering still preserves the entire source timeline.
- Direct users to Jianying/CapCut or another NLE for frame-accurate cutting, character-level trimming, transitions, and final export.
- Preserve the raw ASR result. Store corrections separately or in a derived file with an audit trail.
- Treat LLM curation as an explicit post-ASR stage: it may propose conservative text corrections, quote metadata, and keyword emphasis, but it must not invent speech, alter source timings, or silently delete content. Validate and audit every derived result.
- Do not silently apply the bundled crop/stacking rules to a single-camera, multi-camera, screen-share, or differently letterboxed source. Stop and report the unsupported profile, or adapt and test the geometry first.
- Never start a full render before a `--prepare-only` inspection and short horizontal/vertical sample have passed.

## Workflow

1. Detect dependencies before touching the source. If `ffprobe`/`ffmpeg` or an ASR backend is missing, follow README's capability boundary; there is no automatic substitute for media probing, transcription, or rendering. Do not silently claim that any of them succeeded. Inspect the source with `ffprobe` when available and record the absolute source path, duration, streams, frame rate, audio sample rate, dimensions, pixel format, rotation, and start times. Stop if the video has no playable audio/video stream or the geometry does not match the selected profile.
2. Read [README.md](README.md), especially “兼容性门槛”, “可定制项” and “风险与阻断条件”. Use its data contracts and conservative defaults.
3. Run local Whisper through an available backend. Prefer word/token timestamps and preserve engine/model/language/confidence/preprocessing metadata. Normalize audio with FFmpeg to mono 16 kHz and `aresample=async=1:first_pts=0` before recognition. Do not claim that SRT alone contains character-accurate timing.
4. Save the untouched recognizer output as `*.raw.words.json`.
5. Run or verify the explicit LLM curation stage described in [references/llm-postprocess.md](references/llm-postprocess.md): propose or apply only conservative text corrections, quote metadata, and keyword emphasis; preserve an audit trail and run deterministic validation. If a corrected file with provenance was supplied, verify it instead of re-running the LLM. If no LLM is available, continue only as an explicitly uncurated review, never by fabricating corrections.
6. Select quote candidates using complete meaning, specificity, memorability, and context. Store start/end at sentence or phrase boundaries; make every quote optional in the UI.
7. Analyze speaker view only when the source provides a reliable signal. For conferencing recordings, an active-speaker border is preferred. Use audio energy as a speech/pause gate, not as speaker identity. Fall back to a two-shot when uncertain.
8. Build a conservative shot schedule: start wide, require a stable signal, enforce minimum holds, and periodically return wide. Keep the schedule editable.
9. Generate the review page with `scripts/build_review.py`. Serve it over HTTP with `scripts/serve_review.py`; `file://` is unsupported because browsers restrict local JSON and reliable media seeking needs byte ranges.
10. Verify source duration, range requests, paragraph play, playback highlighting, text correction and undo, quote toggles, shot edits, import/export, and source mismatch rejection. Use [references/acceptance-checklist.md](references/acceptance-checklist.md) as the release gate.
11. Export review settings. Treat the JSON as portable decisions and handoff metadata, not an edit decision list. Never treat browser localStorage as the only backup.
12. If the user explicitly requests rendered output, run `scripts/render_review.py --prepare-only` first, then render short samples in both formats and inspect them before a full render. Render 16:9 and 9:16 separately from the same reviewed settings; keep audio/content duration unchanged unless the user explicitly enables sentence-level `--apply-skips`.

## Included resources

- `README.md`: architecture, every feature’s purpose and implementation, customization points, limitations, and troubleshooting.
- `references/data-contracts.md`: word, quote, analysis, shot-plan, and review-settings schemas.
- `references/llm-postprocess.md`: the post-ASR LLM contract, allowed operations, audit fields, and validation rules.
- `references/acceptance-checklist.md`: required QA before delivery.
- `scripts/build_review.py`: validates inputs and creates a configured review page from the bundled template.
- `scripts/serve_review.py`: local byte-range HTTP server.
- `scripts/validate_review_settings.py`: validates exported settings and enforces the no-cut boundary.
- `scripts/render_review.py`: prepares or renders reviewed horizontal/vertical output with quote and keyword subtitle styling.
- `scripts/package_skill.py`: creates a reproducible zip package while excluding caches and build artifacts.
- `scripts/check_dependencies.py`: checks the selected stage without installing anything or pretending missing capabilities exist.
- `assets/review-template/`: generic HTML/CSS/JavaScript review UI.

Read only the reference needed for the current step. If adapting a project with equivalent scripts, reuse them after confirming they honor these boundaries.
