---
name: settlers-publishing
description: Publish Settlers research findings as Markdown or MDX with recorded charts and public 2D game replays from the design Storybook.
---

Read `docs/publishing.md` for routes, the component registry, and asset contracts.
Read the run record, registered experiment, and verified summary before writing
a numerical claim. Include failures, censoring, limits, and the denominator.

Run `just publish RUN_UUID --match INDEX --slug DESCRIPTIVE-SLUG` to create a
report and compact assets from existing evidence. It verifies hashes and only
accepts a completed game with complete spectator event history. Choose the game
for a stated narrative reason; one highlighted game is not a strength result.
Explain the observation and uncertainty in the generated report. Do not invent
values or omit a failed experiment because the result is inconvenient.

Use `ResearchChart`, `GameReplay`, `ResearchCallout`, and `AgentContext` exactly
as documented. Charts and replays reference JSON asset names through string
props. All visual components, including chart layouts and the flat SVG board,
come from the separate `design/src/components/research/` Storybook and are
exported through `@settlers/design/research`. Research agents may use the existing
registry without a local design checkout. For a new visual capability, implement
and test it in design, then register a typed loader in web; do not implement it
inside MDX or the research repository.

Keep public exhibits bounded and spectator-only. Preserve the replay's sampling
notice, game ID, and source digest. Never publish player observations, credentials,
private logs, or server archives. Put reproduction notes in `AgentContext` and
plain findings in the narrative. Add a dated log entry when evidence changes.

Run `just check`; when web is available, run `npm run check:research` there and
check the resulting page. New components also require design Storybook checks,
keyboard interactions, and a mobile layout check. Generating a local report does
not by itself authorize an external upload or deployment.
