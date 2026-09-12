# Latest-code extraction note

The September 10 project tree was reviewed before publication.

## Promoted into the reusable skill

- The generic review page in `video-editor/vertical-review-20260910/advanced/` matches the repository template and is the canonical reusable implementation.
- Its portable behavior is represented by the template plus the schemas and validators: transcript playback, word highlighting, conservative corrections, quote toggles, emphasis, shot overrides, horizontal/vertical preview, import/export, source mismatch rejection, and the `cuts: []` invariant.
- The acceptance rules from the latest project were retained: HTTP Range serving, duration binding, short-sample verification, source-layout compatibility checks, and explicit NLE handoff.

## Deliberately excluded

- `vertical-studio-20260910/`: an episode-specific continuous-range selector with fixed candidates, copy, output directories and outro text.
- `video-editor/` legacy pages and scripts: older rough-cut/reorder workflows, platform-specific model paths and one-off data assumptions.
- `edit/`, source media, render logs, settings and generated videos: private episode artifacts, not skill inputs.

The excluded pages informed the documentation, but were not copied into the skill because they depend on one episode's timings, visual layout, speaker names and publishing copy.
