# Acceptance checklist

Use this as a release gate. A failed item is a stop condition, not a warning to ignore after the full video has been rendered.

## Compatibility gate

- [ ] Source is explicitly identified as a two-person left/right split-screen or the geometry implementation has been adapted and tested.
- [ ] Source is not silently treated as supported merely because it is 1920×1080; inspect representative frames for panel boundaries, letterboxing, face position, and overlays.
- [ ] The intended delivery formats, subtitle language/font, encoder, and target platform are known before rendering.
- [ ] FFmpeg and ffprobe are available; the selected browser can decode the source codec/container.
- [ ] If local Whisper is required, the selected backend/model and disk/RAM/time budget are available.

## Dependency fallback

- [ ] If FFmpeg/ffprobe is missing, the user has been told that a new page cannot be safely built and no render can be performed; an existing prebuilt page is only a limited review mode.
- [ ] If Whisper/ASR is missing, either valid words JSON was supplied or the workflow is explicitly limited to existing-data review; no new transcription is claimed.
- [ ] Missing dependencies are not replaced by guessed timestamps, a fake successful render, or an unverified cloud upload.

## LLM post-processing

- [ ] Raw ASR JSON is immutable and retained beside any corrected/derived file.
- [ ] LLM corrections are conservative, traceable to segment/asr IDs, and do not change timings or invent speech.
- [ ] LLM output has passed schema/invariant validation before it is used by the review page.
- [ ] Uncertain corrections, quote choices, and emphasis choices remain reviewable and reversible.

## Media and data

- `ffprobe` reports audio and video streams.
- Source duration agrees with words, analysis, plan, and UI config within 0.1 seconds.
- Source start times, rotation, frame rate, dimensions, and audio/video sync have been inspected; a duration match alone is insufficient.
- Raw Whisper output remains untouched; corrections exist only in a derived file or settings.
- Every segment has valid ordered start/end times.
- Plan starts with a `split` shot at 0 seconds and contains no cuts.

## Server and playback

- Page is opened with `http://127.0.0.1`, never `file://`.
- A video range request returns HTTP 206.
- Duration shown by the video element agrees with the config.
- Test paragraph play and text highlighting near the beginning, middle, and end.
- Timing discrepancies are disclosed, not hidden.

## Review functions

- Each transcript paragraph has a play button.
- Search, follow playback, current sentence, rewind, and speed work.
- Text correction survives refresh; undo restores the previous state.
- Quote toggle updates preview and survives refresh.
- Keyword emphasis affects only the selected phrase and survives refresh/export.
- Horizontal preview is 16:9; vertical preview is 9:16 with shorter subtitle lines.
- Preview and ASS render show no more than two subtitle lines; long cues paginate without creating cuts.
- The review queue finds orphan pages/lines, weak grammatical breakpoints, and excessive reading speed; each risk links back to playback.
- Quote styling never adds a corner badge.
- Automatic and fixed-view previews work.
- Add, edit, remove, navigate, and undo shot nodes work.
- Exported settings re-import to the same source.
- Wrong source/duration, invalid shot order, and non-empty cuts are rejected.

## Handoff

- Explain that character highlighting is approximate and never drives cuts.
- Explain what review settings contain and what they do not contain.
- Provide the local URL and startup command.
- Tell the editor to perform character-level cuts and final timing checks in Jianying/CapCut or another NLE.
- Before full rendering, generate a short horizontal and vertical sample from the same settings.
- [ ] Inspect samples at the beginning, first shot change, a quote, a long subtitle, a vertical split view, and the end of the sample.
- [ ] Confirm output duration, audio presence, frame size, subtitle legibility, face crop, shot changes, and A/V sync with `ffprobe` and a player.
- [ ] Full render uses a new output path or `-n`/no-overwrite behavior; source and review JSON remain untouched.
