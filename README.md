---
title: Settlers research
summary: A research notebook and headless arena for stronger Settlers players.
---

# Building a better island player

Settlers rewards more than resource production. A strong player needs a plan for
turning cards into points, a belief about opponents' hands, and a way to adapt
when another road closes an opportunity. This repository is a place to test those
ideas against independent players and keep the evidence, including failures.

Start with the [approaches](approaches/README.md), the [research plan](docs/roadmap.md),
and the [methodology](docs/methodology.md). Read the [status](docs/status.md) before
claiming that a policy is stronger. Published experiments live in `reports/`;
short daily accounts live in `log/`.

The [first arena report](reports/baseline-smoke.mdx) includes a real ten-point
game with a chart and an interactive view from above.

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
python3 -m harness.cli register --players fast eta fast eta --games 40 \
  --hypothesis 'ETA changes win rate against this fixed lineup.' \
  --decision-rule 'Report uncertainty; make no superiority claim from a smoke cohort.'
just run EXPERIMENT_ID
just archive RUN_UUID /path/to/durable/artifacts
just publish RUN_UUID --match 0 --slug first-baseline
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

No GitHub remote or artifact bucket is assumed. Create/connect a GitHub repository
under your chosen owner, install Greptile for that repository, and push this
checkout when ready. The [review configuration](docs/review.md) limits review to
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

## What belongs in Git

Keep policy code, preregistrations, compact run records, reports, and selected
exhibits. Raw per-game rows, event tapes, snapshots, server state, credentials,
and archives stay in ignored `runs/`, `.runtime/`, and `artifacts/` directories.
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
