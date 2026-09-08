# Publishing charts and games

Write ordinary Markdown or MDX in `README.md`, `docs/`, `approaches/`, `reports/`,
or `log/`. The site maps `approaches/example/README.mdx` to
`/research/approaches/example` and `reports/example.mdx` to
`/research/reports/example`. Relative links to Markdown documents are rewritten
to their site routes. Optional frontmatter keys are `title` and `summary`.

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
settlements, cities, robber, current seat, and public points. The range control,
previous/next buttons, and final-position button jump immediately; no autoplay
or 3D animation is involved. Keyboard arrow keys work on the slider.

Only spectator snapshots are eligible. The publisher allowlists public fields
and retains at most 120 observed positions, including endpoints. The caption says
how many snapshots were selected and that intermediate actions may be omitted.
The raw public event tape is separately retained for detailed analysis. A
selected snapshot sequence is not an exhaustive action-by-action reconstruction.

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
