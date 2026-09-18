---
title: Settlers research
summary: Experiments, visual explanations, and a practical guide to building stronger Settlers players.
---

# Building a better settler

We build computer players for Settlers and test how they plan, trade, and act
under uncertainty. Each finding links to its experiment, recorded results, and
next question. The project is [open source](https://github.com/settlerust).

| Start here | What you can do |
| --- | --- |
| [Experiments](/research/experiments) | Follow the findings from newest to oldest |
| [Build a client](/research/client) | Write a player and run a long simulation |
| [Run the server](docs/quickstart.md) | Set up with only the research and server repositories |
| [Research approaches](approaches/README.md) | Explore the decisions and mechanisms being studied |

## LLMs at the Catan table

Four language models played ten complete games using tools to build, negotiate,
and keep private notebooks. DeepSeek won five, Kimi three, GLM two, and Inkling
none. [Read how the arena works and watch the competition](reports/llm-arena.mdx),
including the agents’ conversations, returned reasoning, and evolving notes.

## The current baseline

**`ntuple-leaf`** combines expectimax search with [learned position values](docs/concepts.md#learned-leaf). In
its registered protocol comparison, it won 46 of 80 games against 25 for the
previous hand-written-leaf search. All 80 games completed.

<ResearchChart asset="ntuple-leaf-protocol-wins" />

That result concerns one lineup and one relative seating scheme. Read the
[experiment and replay](reports/ntuple-leaf-protocol.mdx), the later
[seating findings](reports/arena-seating.mdx), and the [current evidence boundary](docs/status.md)
before generalizing. New comparisons use both relative orders of the candidate
and reference. The [latest retests](reports/tables-retest.mdx) identify a promising
leaf blend; it still needs a protocol cohort before replacing this baseline.

## Explore the research

<StrategyAtlas asset="strategy-atlas" />

Each approach connects a game decision to a proposed mechanism and an experiment.
The [experiment timeline](/research/experiments) shows what has been tested;
the [roadmap](docs/roadmap.md) shows what remains open.

<AgentContext title="Run matches and contribute">

## Your first match

Install Python 3.11+, Rust 1.96+, and `just`. Keep the server checkout beside this
repository as `../server`, or set `SETTLERS_SERVER_DIR` to its absolute path.

```sh
# From research/. Leave the server in this terminal.
just setup
just tables
just server
```

```sh
# In another terminal, also from research/.
just doctor
just match ntuple-leaf expectimax-v2-plan ntuple-leaf expectimax-v2-plan --games 1
```

The [server guide](docs/quickstart.md) explains storage and optional fast/ETA
opponents. The [client guide](/research/client) includes a working Python policy,
registration, mirrored cohorts, parallel runs, and result inspection.

## Keep the research reproducible

The harness has no third-party Python dependencies. It runs independently of
`web` and `design`; an all-stdio lineup needs only Python and a reachable server.
Locally built Rust players need the server checkout, and the learned baseline
also needs the committed tables unpacked with `just tables`.

Register a study before collecting evidence. Keep frozen protocols, compact
records, and selected public exhibits in Git. Raw runs, server state,
credentials, and archives stay in ignored `runs/`, `.runtime/`, and `artifacts/`.
Use `just archive` to retain a verified bundle and its receipt. Temporary research
worktrees belong inside `.worktrees/` in this repository.

Follow the [research workflow](docs/research-workflow.md) to update the owning
study and dated log, then run `just notebook` and `just check`. The
[publishing guide](docs/publishing.md) explains sourced charts and game replays.
When the separate website checkout is available, `just site-check` validates
its routes and MDX. The website renders these documents under `/research`;
running simulations does not require building or deploying it.

The canonical source remote is `settlerust/research`. No artifact bucket is
assumed. Agent entry points are in `AGENTS.md` and `.agents/skills/`.

</AgentContext>
