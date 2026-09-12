# LLM post-processing contract

The technical pipeline produces evidence; the LLM performs a bounded editorial/curation pass on top of that evidence. This stage is required whenever the workflow promises corrected text, quote candidates, keyword emphasis, or a human-readable handoff. It is not a second ASR engine and it is not authorized to edit the media timeline.

## Pipeline position

```text
source media
  -> ffprobe / audio normalization / ASR / visual analysis
  -> immutable raw words + analysis
  -> LLM curation with audit trail
  -> deterministic schema validation
  -> human review page
  -> optional sample render
```

If the LLM stage is unavailable, the workflow may continue with raw text and a visible `uncurated` status. It must not silently apply guessed corrections or claim that the text has been reviewed.

## Allowed operations

The LLM may:

- propose clear ASR corrections for names, terms, homophones, punctuation, and obvious segmentation artifacts;
- preserve the spoken wording while improving display punctuation or line-break-friendly text;
- propose quote titles/reasons whose start/end are copied from existing sentence or phrase boundaries;
- propose keyword emphasis only for literal substrings of the effective segment text;
- create a review queue for low-confidence or context-dependent items.

The LLM must not:

- invent words that are not supported by the audio/transcript context;
- rewrite a speaker's meaning, tone, stance, or speaking style without an explicit editorial request;
- change `start`/`end`, token/character timing, source duration, or speaker identity;
- turn a corrected sentence into a cut, or populate `cuts`;
- remove fillers, pauses, repeats, cold opens, or content unless the user separately authorizes editorial deletion;
- present quote quality, speaker identity, or ASR confidence as fact when it is only a model judgment.

## Required inputs

At minimum provide:

- immutable `*.raw.words.json`;
- the source identity and duration;
- optional glossary, speaker names, shownotes, and user style rules;
- optional visual/audio analysis, but never use RMS alone to infer speaker identity.

The LLM should receive the relevant segment context, not only an isolated short sentence, when correcting names or meaning. For a proposed change, it should be able to cite the segment array index and, when available, `asr_index`.

## Derived output and audit trail

Keep the raw file untouched. A corrected words file may change display text but should retain the original segment timing and IDs. Store a separate correction log such as:

```json
{
  "source_raw": "episode.raw.words.json",
  "source_duration": 1657.033,
  "status": "reviewed",
  "corrections": [{
    "segment_index": 12,
    "asr_index": 12,
    "original_text": "原识别",
    "proposed_text": "校正文本",
    "final_text": "校正文本",
    "action": "accepted",
    "reason": "专有名词，与上下文和音频一致",
    "confidence": "high",
    "reviewer": "human-or-llm",
    "created_at": "2026-09-06T00:00:00Z"
  }]
}
```

The exact log schema may be adapted, but it must preserve original/final text, stable segment references, reason, status, and provenance. If a correction changes character count, character highlighting becomes approximate within that segment's original time range; this must be disclosed in the handoff.

## Deterministic validation before review

Before loading the derived file:

- every segment remains non-empty and ordered;
- every `start`/`end` remains within the same source duration;
- segment count and stable IDs are unchanged unless a separate, auditable segmentation migration is performed;
- audio/video/source duration is unchanged;
- `cuts` remains `[]` and `preserve_all_content` remains true;
- every emphasis is a literal substring of the effective edited text;
- quote intervals remain within the source timeline and remain optional;
- unresolved or rejected proposals are not silently applied.

The human reviewer must be able to compare original and corrected text and undo the correction. The final editor still checks names, numbers, claims, and legal/sensitive wording against the audio.
