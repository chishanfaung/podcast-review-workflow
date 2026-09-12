# Data contracts

Times are floating-point seconds on the untouched source timeline. All lists must be sorted by time.

## Recommended provenance

The required schema below is intentionally small, but a production ASR adapter should also preserve provenance rather than only exporting text:

```json
{
  "asr": {
    "engine": "faster-whisper",
    "engine_version": "record-installed-version",
    "model": "large-v3",
    "model_source": "Systran/Hugging Face or local path",
    "language": "zh",
    "language_probability": 0.99,
    "audio_preprocess": {"sample_rate": 16000, "channels": 1, "timestamps_zeroed": true}
  }
}
```

Optional segment evidence such as `avg_logprob`, `no_speech_prob`, `compression_ratio`, `temperature`, and `words[].probability` is useful for prioritizing human review. It is evidence, not an automatic authorization to cut or delete content.

## Words

```json
{
  "version": 1,
  "source": "/absolute/source.mov",
  "segments": [{
    "text": "识别文本", "start": 0.0, "end": 2.4, "asr_index": 0,
    "tokens": [{"text": "识别", "start": 0.1, "end": 0.8, "probability": 0.98}],
    "chars": [{"text": "识", "start": 0.1, "end": 0.4, "token_index": 0}]
  }]
}
```

Required per segment: non-empty `text`, finite `start`, finite `end`, and `0 <= start < end <= duration`. Segments may touch but must not overlap materially. `tokens` and `chars` are optional and are only for review highlighting.

## Analysis

```json
{
  "source": "/absolute/source.mov", "duration": 1657.033, "sample_interval": 0.5,
  "samples": [{"time": 0.0, "left": 0, "right": 685, "rms": 0.037, "side": "right"}]
}
```

`side` is one of `left`, `right`, `split`. Pixel counts and RMS are diagnostic. RMS gates speech/pause; it does not identify a speaker.

## Plan

```json
{
  "source": "/absolute/source.mov", "source_duration": 1657.033,
  "cuts": [], "preserve_all_content": true,
  "preview_shots": [
    {"source_time": 0.0, "view": "split", "reason": "opening"},
    {"source_time": 5.0, "view": "right", "reason": "stable active-speaker border"}
  ],
  "quotes": [{
    "id": "quote-01", "title": "短标题", "reason": "为什么值得强调",
    "start": 130.74, "end": 140.44, "text": "金句原文", "asr_indexes": [41, 42]
  }]
}
```

The first shot starts at 0. Shot times are strictly increasing and less than duration. `cuts` must be `[]`, and `preserve_all_content` must be `true`.

## Review config

`build_review.py` writes `review-config.js` and binds one page to its files. It contains `id`, `title`, `sourceName`, `duration`, URL fields, speaker names, and optional ASR IDs for review.

## Exported review settings

```json
{
  "version": 1, "source": "final.mov", "duration": 1657.033,
  "edits": {"12": "校正后的短句"},
  "emphases": {"12": ["重点词", "数字"]}, "disabledQuotes": ["quote-03"],
  "skipSegments": [34, 35],
  "shotOverrides": null,
  "preview_shots": [{"source_time": 0.0, "view": "split", "reason": "opening"}],
  "cuts": [], "exported_at": "2026-09-04T00:00:00.000Z"
}
```

`edits`, `emphases` keys and `skipSegments` values use the segment array index, not `asr_index`. Every emphasis must be a non-empty substring of the effective edited text. `skipSegments` marks complete short sentences to skip during browser playback; it is not a character-level cut list. A consumer uses `shotOverrides` when non-null, otherwise the plan's original `preview_shots`. Any non-empty `cuts` value is invalid.
