---
title: "3. Play against computer policies"
summary: Register your agent, choose fast, ETA, or liquidity opponents, run matches, and inspect actions and conversation in a replay.
---

# Put your agent at the table

You now have a process that reads an observation and returns a command. Register it so the harness can create one independent instance per seat.

## Register your policy

Create `policies/my_agent.py` using the previous page's example, then add this entry to `policies/registry.toml`:

```toml
[my-agent]
transport = "stdio"
command = ["{python}", "policies/my_agent.py"]
description = "My first observation-driven player"
```

Commands are argument arrays, executed from the research checkout. The harness supplies the Python interpreter and manages each seat's identity, requests, and retries.

## Choose opponents

| Policy | What it does | Preparation |
| --- | --- | --- |
| `legal-first` | Picks from a fixed priority list of legal actions; useful for checking the protocol | Included Python example |
| `fast` | Uses the existing Rust fast builder with its trading wrapper | `just setup` |
| `eta` | Plans with estimated resource acquisition time and a trading wrapper | `just setup` |
| `liquidity` | Experimental exchange-aware acquisition estimator; did not earn promotion in the first evaluation | `just build-liquidity` |
| `eta-control`, `fast-control` | Frozen study comparators sharing the liquidity runner and protocol adaptations | `just build-liquidity` |

These are policy descriptions, not a general strength ranking. Start with a small, fixed lineup:

```sh
just policies
just match my-agent fast eta legal-first --games 4
```

Each policy appears once in each seat. The server chooses the opening player and randomness independently. To check the bundled Python example before writing your own, use:

```sh
just match legal-first fast eta fast --games 4
```

A stdio adapter gets one decision at a time. Remote Rust policies own their connections and may act concurrently. Keep this difference fixed when comparing negotiation timing.

## Read what happened

The result table lists completion counts, wins, and public points for each competitor slot. A failure, deadline, or interruption remains in the record and stops the remaining schedule. Fix it before registering another run; do not count an unfinished game as a loss.

To watch a live research table, open `/game/GAME_ID` in a web client connected to the same server. To retain a completed game as a notebook exhibit, use the run UUID printed by the harness:

```sh
just publish RUN_UUID --match 0 --slug my-first-game
just check
```

The resulting report includes a public board replay, actions, and any public conversation captured in the event tape. The board uses selected observed positions; the timeline explains the events between them. Read the [first arena replay](../reports/baseline-smoke.mdx) for an existing example. Publishing a local report does not launch or deploy the website.

## Turn the smoke test into research

Once your policy reliably finishes games, use the [Research experiment program](experiment-program.md) to register a hypothesis, freeze opponents and budgets, and keep a fresh evaluation cohort. The [Roadmap](roadmap.md) identifies the open questions those experiments can resolve.

Previous: [2. Write your first policy](protocol.md).
