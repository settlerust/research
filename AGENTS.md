<!-- BEGIN SETTLERS HARNESS -->
## Settlers delivery contract

This is the `research` repository in the Settlers workspace. Read [.agents/rules/product.md](.agents/rules/product.md) for its ownership, dependency and deployment map, and [.agents/rules/delivery.md](.agents/rules/delivery.md) before making or shipping changes.

- **Current phase: stabilization.** Direct, non-force pushes to `dev` are allowed until the user declares the test version stable; dev deployments still run through CI/CD. Do not require a PR or enable protection that blocks this authorized phase.
- For PR-based work, implement on `feature/<slug>`, `fix/<slug>`, `improvement/<slug>`, `chore/<slug>`, or another documented type, based on `origin/dev`. Share the exact branch name across coordinated repositories. No leading `/`.
- Ordinary PRs target `dev`; release PRs are `dev` → `main`. Use this repository's `.github/PULL_REQUEST_TEMPLATE.md` or `.github/PULL_REQUEST_TEMPLATE/release.md`, with explicit Upstream and Downstream PR links (or `None`).
- Use explicit push refspecs. Never push directly to `main` or force-push. After stability is declared, deliver changes to `dev` through topic PRs. Preserve unrelated edits and existing authorization boundaries.
- Dev builds use dependency `dev` branches; production uses `main`. Validate the actual deployment owner's run and endpoint, not merely a dispatch job. Merge compatible upstream changes before consumers.
- For implementation/PR work, read [.agents/skills/settlers-change/SKILL.md](.agents/skills/settlers-change/SKILL.md). For release work, read [.agents/skills/settlers-release/SKILL.md](.agents/skills/settlers-release/SKILL.md).

These rules and skills are portable copies maintained in `settlerust/scripts` under `agent-harness/`. In the sibling workspace, regenerate with `python3 ../scripts/sync-agent-harness.py --write`; preserve the repository-specific instructions below.
<!-- END SETTLERS HARNESS -->

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
  The one exception is the frozen baseline tables in `tables/` (xz-compressed,
  digests in `tables/SHA256SUMS`); `just tables` unpacks them into `artifacts/ntuple/`.
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
