# Publishing charts and games

Write ordinary Markdown or MDX in `README.md`, `docs/`, `approaches/`, `reports/`,
or `log/`. The site maps `approaches/example/README.mdx` to
`/research/approaches/example` and `reports/example.mdx` to
`/research/reports/example`. Relative links to Markdown documents are rewritten
to their site routes. Frontmatter supplies `title` and `summary`. Experiment reports also require a quoted `date: "YYYY-MM-DD"`. The [experiment timeline](/research/experiments) lists all reports newest first, with compact previews drawn from their first recorded chart or plot. Run records stay available for linked reproduction notes but are excluded from browsing and search.

Use the project’s `settlers-writing-style` skill for research prose and captions. Code fences should name their language (`python`, `sh`, `rust`, `json`, or `mdx`). Shiki highlights them during server rendering; unknown languages remain plain text. Inline code keeps its compact style.

For the visual writing workflow, animated approach pages, new plot schemas, and teaching examples, read [Communicate with evidence](visual-publishing.mdx). New ideas follow the [approach template](approach-template.md).

## Mathematics in prose

Use `$...$` for inline TeX and `$$` on separate lines for a display equation. MathJax renders both in research pages and agent notebooks. For example, the probability of rolling a seven is $P(S=7)=\frac{6}{36}=\frac{1}{6}$.

```md
The probability of rolling a seven is $P(S=7)=\frac{6}{36}=\frac{1}{6}$.

$$
\mathbb{E}[X] = \sum_{i=1}^{n} p_i x_i
$$
```

The display equation above renders as:

$$
\mathbb{E}[X] = \sum_{i=1}^{n} p_i x_i
$$

Fractions, subscripts, Greek letters, matrices, and aligned equations are supported. Use `\mathrm{ms}` for units and `\ce{H2O}` for chemical notation inside math delimiters. A fenced `math` block also creates a display equation. Ordinary code fences and inline code preserve literal TeX. Escape a currency dollar sign as `\$`; use braces normally inside math, such as `$x_{t+1}$`.

Define symbols and units next to the equation. The site typesets formulas on the server, so they are present before browser JavaScript runs. Long display equations scroll within the prose on narrow screens. TeX that loads extensions, inserts HTML, or creates URLs is not supported; invalid formulas fail the content check. No imports or scripts are needed in a document.

## Use the design components

The rendering registry comes from `@settlers/design/research`. Every visual
implementation and story lives in the separate design repository, under
`src/components/research/`. The web app only loads documents/assets and binds
them to imported components. These are the supported MDX embeds:

```mdx
<ResearchCallout title="What this result establishes">
This run checks the protocol workflow. It does not rank the policies.
</ResearchCallout>

<ResearchChart asset="baseline-smoke-wins" />

<GameReplay asset="baseline-smoke-game" />

<AgentContext>
Put reproduction commands and implementation notes here.
</AgentContext>
```

The asset names above are examples. Generate actual assets with:

```sh
just publish RUN_UUID --match 0 --slug baseline-smoke
```

This verifies the finalized run inventory, selects a completed game with complete
public event history, and creates `reports/baseline-smoke.mdx` plus two small
JSON files under `content/assets/`. It refuses overwrites. Review the generated
report, explain why you chose the game, and add the scientific interpretation.
Keep aggregate evidence separate from an illustrative game. Never invent a
number in a chart or narrative.

## Charts

`ResearchChart` draws recorded per-competitor win rates and 95% Wilson intervals.
Each row carries a label, value, interval, and completed-game count. The caption
preserves run ID and the planned/completed denominator. If you need a different
chart family, add a typed component and meaningful Storybook states in design,
then add its asset validator and binding in web. Do not smuggle a new chart
implementation into an MDX expression.

## Flat replay

`GameReplay` draws the real topology in SVG: terrain, number tokens, ports, roads,
settlements, cities, and robber. Player cards show recorded names, public card counts,
points, pieces, knights, road length, and awards. The board includes dice probabilities,
the last recorded roll, and bank supply. Older recordings that contain only bank
availability show availability instead of inventing exact counts. Play/pause advances
between selected snapshots; speed controls change the reading pace. Previous,
next, final position, and the keyboard-accessible slider pause playback and seek.
New pieces briefly settle into place and new roads draw along their edges.
Reduced-motion preferences turn these effects off. On narrow screens, Enlarge board
opens a larger, horizontally scrollable view; Fit board restores the overview.

The activity panel includes public rule actions, trades, and public conversation
through the displayed position. Use This step for the interval since the previous
snapshot, Full history for everything so far, and Conversation only to isolate
messages. A purchase never reveals an unplayed development card. Directed chat
and research-only theft details are excluded even when an old tape contains them.

New captures retain each seated member’s public name, connection status, and readiness
with every spectator frame. Older captures recover these fields from public joined,
presence, and ready events up to that frame’s version. If a name was never recorded,
the viewer uses a color label and says “Name not recorded.” Never invent a name, avatar,
or model identity. Private identity fields and hidden hands are not replay metadata.

Only spectator snapshots are eligible. The publisher retains at most 120 observed
positions including endpoints and at most 6000 public activity entries. Board
changes between snapshots are grouped; these are not reconstructed intermediate
positions. The server's recorded event sequences bound each interval. SHA-256
digests identify both frame and event sources. Existing exhibits without activity
remain readable with a clear notice. All assets must stay below 1 MB.

## Review and validation

Markdown does not accept arbitrary HTML, imports, scripts, JavaScript expressions,
style attributes, or custom components. Rich props are string asset references;
data belongs in validated assets. Curated assets must be below 1 MB each and are
excluded from Greptile review. Bulk runs never become MDX assets automatically.

Run `just check`. In a checkout with the website and design repositories, run
the website's `npm run check:research`, typecheck, lint, tests, build, and research
Playwright tests. For component changes also run design's typecheck, lint,
Storybook interaction tests, and Storybook build. Check a narrow viewport and
keyboard operation. An independent research agent can write a report using the
existing registry without modifying or installing the website.

The [compact experiment report template](research-report-template.mdx) gives the structure used by the first policy study, plus the next evidence components worth building.

## Release handoff

Before publication, file the report in its owning study, append its dated
interpretation, and update the outcome and next step. `just notebook` refreshes
the experiment log, approach study sections, and roadmap. `just check` enforces
complete filing; `just site-check` also compiles the actual website documents and
validates their assets. The website runs this notebook check in prebuild, before
staging content, so a production build cannot silently ship stale study sections.
Build environments need Python 3.11+ as well as the web toolchain.

Integrate the research source and documentation together, then push when the task
authorizes it. The existing `service/.github/workflows/deploy.yml` checks out
`settlerust/research` with the other four repositories: `dev` for the development
stage and `main` for production. Its “Review or deploy Settlers” workflow defaults
to a diff; choose the deploy operation when a release is authorized. A research
push alone currently runs checks and does not trigger a site deployment.

The web build copies only discovered Markdown/MDX and validated curated JSON into
`.research-content`. Skills, study TOML, `.worktrees`, raw runs, and runtime state
stay out of the deployed artifact. Web renders the staged content in production;
the site does not read the live research working directory after deployment.
After a release, verify the changed experiment and approach routes. Report the
research commit, release status, and verified URL, or clearly state that the work
is locally validated and awaiting its release. Existing user authorization governs
commit, push, and deployment; generating a report does not imply any of them.

## Inline results and the experiment timeline

Use counts to give a win rate a visible denominator. Comparisons use differences
in wins per game, with their recorded 95% interval:

```mdx
<WinRate value="46" total="80" label="Learned leaf" />
<ResultComparison value="0.066" low="0.024" high="0.107" />
```

These examples come from the learned-leaf protocol cohort and the quarter-blend
engine comparison respectively; they are different experiments. Keep the source,
lineup, completed denominator, and any failures in the surrounding explanation.
The comparison is green only when the whole interval is above zero, red when it
is below, and gray when it includes zero. Focus or hover to read the interval.
All numeric props are quoted literals; the validator rejects impossible counts
and intervals. A percentage is descriptive, not a significance test.

`<ExperimentTimeline />` loads every report, sorted by its publication date with
title as the tie-breaker. Its preview uses the first recorded chart or measured
non-heatmap plot in the report; illustrative fixtures never become result previews.
Each preview labels its units and shows at most three comparisons. Search filters
titles and summaries. Reports without charts still appear. Keep frontmatter
summaries short enough to explain the finding in one or two sentences.

`<ResearchWorkflow />` shows the client/server observation loop. Use
`<AgentContext title="Methods and reproduction">` to keep commands, audits,
and detailed study ledgers available without interrupting the main explanation.
The client guide lives at `/research/client`; the old experiment-log address
redirects to `/research/experiments`.

## Readable links and previews

Give run links a useful label such as [the 80-game protocol cohort](/research/records/runs/de39917c-55da-40ad-a53a-5b8588898810).
The UUID belongs in the destination, never in the visible label. The same rule
applies to experiment registrations and audit tables. Keep exact IDs in command
arguments only where needed to reproduce a run, inside `AgentContext`.

Internal research links show a short summary on hover or keyboard focus. Run
previews include status and planned, completed, incomplete, and unplayed counts;
approach previews use the page's title and summary. Links to a heading show that
section's explanation. First prose mentions of the common terms in
[Research concepts](concepts.md) receive definition links automatically.
Escape dismisses the preview. Clicking or tapping still opens the destination.
External links keep their normal behavior and do not fetch third-party previews.

Older chart assets keep their original IDs and hashes for verification; the
renderer presents known run identifiers as readable record links. The full run
page keeps the original record behind a provenance disclosure.
