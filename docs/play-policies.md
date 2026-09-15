---
title: Choose research opponents
summary: Choose the current learned-leaf baseline, hand-written search, or optional builders, then run and inspect a fixed lineup.
---

# Choose research opponents

Start with **`ntuple-leaf`**, the current protocol baseline. It is the
`expectimax-v2-plan` search with learned position values. The
[client guide](client.mdx) takes your own process from its first move to a
registered simulation; this page helps choose the other seats.

## Current searches

| Policy | What changes | Preparation |
| --- | --- | --- |
| `ntuple-leaf` | Current protocol baseline: [learned leaf](concepts.md#learned-leaf), depth 3, 1.5 s search budget | `just setup` and `just tables` |
| `expectimax-v2-plan` | Previous protocol baseline: same frozen search with a hand-written leaf | `just setup` |
| `expectimax-v2` | Tunable search at its default depth-2 configuration | `just setup` |
| `ntuple-leaf-deep` | Depth cap 4 and 4 s budget; did not improve on `ntuple-leaf` in its protocol cohort | `just setup` and `just tables` |
| `ntuple-leaf-tt` | Adds a cache retained across a turn; protocol strength comparison was inconclusive | `just setup` and `just tables` |

The [evidence boundary](status.md) records what these comparisons established.
The deeper and cached variants are available for investigation; they have not
replaced the baseline.

```sh
just match ntuple-leaf expectimax-v2-plan ntuple-leaf expectimax-v2-plan --games 4
```

## Builders and historical references

| Policy | Use | Preparation |
| --- | --- | --- |
| `fast` | Simple Rust builder with a trading wrapper | `just setup` |
| `eta` | Builder using estimated resource acquisition time | `just setup` |
| `legal-first` | Minimal Python adapter for checking legality and client plumbing | Included |
| `expectimax-v1` | Frozen reference search | `just setup` |
| `expectimax-v2-deep` | Historical depth-3, 1.5 s candidate with more scenarios and sampled worlds | `just setup` |
| `liquidity` | Exchange-aware estimator from the first study; did not earn promotion | `just build-liquidity` |
| `eta-control`, `fast-control` | Frozen comparators sharing the liquidity study's runner | `just build-liquidity` |

Use builders when reproducing earlier lineups or studying behavior against
simpler opponents:

```sh
just match ntuple-leaf expectimax-v2-plan eta fast --games 4
```

`just policies` prints the complete registry. Commands run from the research
checkout; each seat gets a separate process and credential, even when a policy
name appears twice.

## Read the result

Each row represents a **competitor slot**, not every instance of that policy
combined. Four games rotate the lineup through the seats. They check the setup;
a strength study also needs frozen budgets, fresh seeds, and both relative
orders of the candidate and reference.

The result keeps completed, incomplete, and unplayed games separate. A failed
match stops new work, and in-flight parallel games finish before the result is
finalized. Read `runs/RUN_UUID/summary.json` and the individual `result.json`
files before registering another run.

For a recorded example, open the [learned-leaf game](../reports/ntuple-leaf-protocol.mdx).
To watch your own game live, a web client must connect to the same server and
open `/game/GAME_ID`. That optional viewer is separate from running experiments
with only the two repositories.

Continue with [the client and simulation guide](client.mdx#4-register-a-longer-simulation)
or [publish a selected replay](publishing.md).
