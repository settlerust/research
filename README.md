---
title: Settlers research
summary: A research notebook and headless arena for stronger Settlers players.
---

# Building a better settler

We test computer policies for Settlers, focusing on resource planning, uncertainty, trading, and adaptation.

New here? Follow the three-step agent tutorial: [connect to the server](docs/quickstart.md), [write a policy](docs/protocol.md), then [play against computer opponents](docs/play-policies.md). Use the [Research experiment program](docs/experiment-program.md) to design a fair comparison and the [Roadmap](docs/roadmap.md) to explore the open questions.

<ResearchCallout title="First policy experiment · 80 complete games">
An exchange-aware ETA candidate won 25% of games against the control's 32.5%.
It did not earn promotion. Read the [visual experiment report](reports/liquidity-baseline.mdx)
for the result, mechanism, diagnostics and retained failures.
</ResearchCallout>

<StrategyAtlas asset="strategy-atlas" />

## Research approaches

Each approach describes a decision, a mechanism, and a proposed comparison.

These sixteen broad directions are proposals. A narrow exchange-planning ablation is now implemented and evaluated; it did not establish an improvement. Read the [evidence boundary](docs/status.md) before making a strength claim. The [first arena report](reports/baseline-smoke.mdx) contains a recorded ten-point game and a real smoke-cohort chart.

Follow the dated [experiment log](log/experiments.mdx) for investigations and their
next steps. The [research workflow](docs/research-workflow.md) explains how agents
file studies under an approach and keep these pages current.

<AgentContext>

## Run a match

Requires Python 3.11+, `just`, and a reachable Settlers protocol v1 server.
The Python harness has no third-party dependencies. Rust is needed only to build
the local server and the bundled `fast` and `eta` opponents.

```sh
# From this repository. A separate server checkout defaults to ../server.
export SETTLERS_SERVER_DIR=/path/to/settlers/server
just setup
just server                 # foreground; http://127.0.0.1:5555
```

In another terminal:

```sh
just doctor
just policies
just match fast eta fast eta --games 4
# A research-owned Python player can join the same lineup:
just match legal-first eta fast eta --games 4
```

The harness registers a smoke experiment before playing, creates separate
credentials and processes for every seat, rotates the lineup, and prints a result
table. Four matches are a plumbing check, not a strength ranking. `Ctrl-C` records
an interruption and stops the owned players. The server retains the game; its
later timeout actions are outside that run's evidence.

## Register research

```sh
just study log/eta-comparison --title 'ETA at a fixed table' \
  --question 'How does ETA compare against this frozen opponent lineup?'
python3 -m harness.cli register --study log/eta-comparison --players fast eta fast eta --games 40 \
  --hypothesis 'ETA changes win rate against this fixed lineup.' \
  --decision-rule 'Report uncertainty; make no superiority claim from a smoke cohort.'
just run EXPERIMENT_ID
just archive RUN_UUID /path/to/durable/artifacts
just publish RUN_UUID --match 0 --slug first-baseline
# Interpret the run, update its study and dated log, then refresh the notebook.
just notebook
just check
```

Edit a new experiment's settings and stop rules **before its first run**. Keep
completed protocols immutable. To change a configuration, create a new experiment.
For shell-sensitive arguments, use `python3 -m harness.cli` directly.

## Standalone repository

This directory has its own Git repository. It can be moved or cloned without
`web` or `design`; there are no symlinks, submodules, or Python path imports into
its siblings. Set `SETTLERS_SERVER_DIR` for locally built Rust opponents, or
`SETTLERS_SERVER_URL` for an already running server. An all-stdio lineup needs no
local Rust checkout. Policy commands and source live in `policies/`.

The canonical source remote is `settlerust/research`. No artifact bucket is
assumed. The [review configuration](docs/review.md) limits review to
authored Rust, TypeScript/TSX, and Python files.

## Publish a research notebook

The separate Next.js application reads this checkout at `../research`, or at
`SETTLERS_RESEARCH_DIR`, and renders Markdown/MDX under `/research`. Rebuild the
web app after changing content for a production deployment. It needs the checkout
at build time; no research server is needed to read the site.

Rich components come exclusively from `@settlers/design` and have Storybook
stories. [Publishing instructions](docs/publishing.md) explain charts, selected
flat 2D replays, and provenance. Agent entry points are in `AGENTS.md` and
`.agents/skills/`.

`just notebook` refreshes the experiment index and study sections in approaches
and the roadmap. `just site-check` checks their filing and compiles the site's
MDX/assets. Research CI and web prebuild reject stale or unfiled evidence.

## What belongs in Git

Keep policy code, preregistrations, compact run records, reports, and selected
exhibits. Raw per-game rows, event tapes, snapshots, server state, credentials,
and archives stay in ignored `runs/`, `.runtime/`, and `artifacts/` directories.
Temporary research worktrees stay under ignored `.worktrees/` inside this checkout.
`just archive` makes an immutable, hash-verified bundle without credentials or
private process logs; its receipt says where it actually exists. Git tracks the
evidence trail, not thousands of generated data files.

### Watching a live research game

The harness creates explicit agent-only research tables and joins each policy with
its own `join_agent` command and JWT. Open `/game/<gameId>` in a web client configured
for the same game server to watch. Research spectators receive all current hands;
policies still receive only their own redacted observation. The game ID is printed
in the match record. The default research server port and web development server
port may differ; configure them to use the same server for live discovery.

</AgentContext>
