# Settlers research agent contract

This is an independent research repository. Policies play the authoritative
Settlers protocol; the harness does not simulate outcomes.

- For inventing, implementing, or evaluating a strategy, read
  `.agents/skills/settlers-experiment/SKILL.md`, then `docs/status.md` and
  `docs/methodology.md`.
- For writing up results or embedding charts/replays, read
  `.agents/skills/settlers-publishing/SKILL.md` and `docs/publishing.md`.
- Register a falsifiable hypothesis, fixed lineup, game count, budgets, and decision
  rule before collecting evidence. Never rewrite a completed experiment or result.
- Each policy sees only its own protocol observation and filtered events. No
  other credentials, hidden state, server archives, or future randomness may enter
  a deployable policy. No seed is exposed by the public API.
- Work in an isolated branch/worktree for a bounded experiment. Use generated
  UUIDs; run directories are exclusive. Integrate shared status and daily notes
  after contributions are reviewed. Do not launch other agents unless requested.
- Keep failures, invalid runs, censoring, and interruptions. Stop on a failed
  match and investigate before spending the remaining run budget. Incomplete
  games are not losses and must remain visible beside the completed denominator.
- Use `just check`. For policy changes, also run a small protocol match before a
  larger experiment. A smoke run is never evidence of strategic superiority.
- Keep data out of Git. Use `just archive` and preserve the verified receipt.
  Publishing locally does not authorize uploading data to an external service.
- After substantive research, append a dated entry to `log/YYYY-MM-DD.mdx` and
  record the hypothesis, run IDs, interpretation, failures, and actual agent/model
  attribution (or `unknown`). Maintenance alone needs no research credit record.
- Every visual component belongs to the separate design Storybook. MDX may only
  embed registered design components; do not add ad hoc HTML, styles, scripts,
  imports, or component implementations to a research report.
