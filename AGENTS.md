# Settlers research agent contract

This is an independent research repository. Policies play the authoritative
Settlers protocol; the harness does not simulate outcomes.

- The user prefers simple, human design and plain, useful copy. Do not add decorative slogans, eyebrow text, generic notices, or repeated disclaimers. Every visible sentence should explain the content, a finding, a relevant limitation, or a control. State proposal/evidence status briefly where it matters, preferably in the prose or a section heading rather than a repeated callout. Do not fill empty space with text.
- For page text, captions, and interface copy, use `.agents/skills/settlers-writing-style/SKILL.md`. Avoid em dashes and unnecessary lists. Diagram captions describe what is shown in one short sentence. Illustrative animations loop gently without play/pause buttons and respect reduced motion; game replay playback is a separate timeline control.
- For starting, continuing, integrating, or documenting research, read
  `.agents/skills/settlers-research-workflow/SKILL.md`. All research belongs in
  this canonical directory; temporary worktrees belong in `.worktrees/`, never
  sibling `research-*` directories. Every experiment and report has one owning
  approach study or cross-cutting study in the experiment log.
- For inventing, implementing, or evaluating a strategy, read
  `.agents/skills/settlers-experiment/SKILL.md`, then `docs/status.md` and
  `docs/experiment-program.md`.
- For writing up results or embedding charts/replays, read
  `.agents/skills/settlers-publishing/SKILL.md` and `docs/publishing.md`.
- Register a falsifiable hypothesis, fixed lineup, game count, budgets, and decision
  rule before collecting evidence. Never rewrite a completed experiment or result.
- Each policy sees only its own protocol observation and filtered events. No
  other credentials, hidden state, server archives, or future randomness may enter
  a deployable policy. No seed is exposed by the public API.
- Work in an isolated branch or use `just worktree NAME` for a bounded experiment. Use generated
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
- Update the owning study's metadata, report/log links, conclusion, and next step
  alongside the evidence. Run `just notebook`, `just check`, and `just site-check`
  when web is present. Integrate the refreshed approach, experiment log, roadmap,
  and any changed evidence boundary together; the site build rejects stale filing.
- Every visual component belongs to the separate design Storybook. MDX may only
  embed registered design components; do not add ad hoc HTML, styles, scripts,
  imports, or component implementations to a research report.

- New strategy ideas follow `docs/approach-template.md`: each has its own registered animated SVG, a concrete decision, a falsifiable study, and an explicit evidence status. Read `docs/experiment-program.md` for the shared design and `docs/visual-publishing.mdx` for figure selection. Prefer a mechanism figure and a sourced chart over long prose; put reproduction detail in `AgentContext`.
- Distinguish belief updates, changes to the value function, and bounded social reranking. Preserve the fixed expectimax reference and its heuristic units. A model-call eligibility threshold is not an enforced concession cap.
- Label conceptual figures, synthetic fixtures, and exact calculations. Never present them as measured outcomes. Add catalogue entries and matching pages together; extend the design registry and web validator when a new visual is needed.
