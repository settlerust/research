---
title: Run the research server
summary: Start a local server and play with the current search policies using only the research and server repositories.
---

# Run the research server

You need **two repositories**, Python 3.11+, Rust 1.96+, and `just`. The Python
harness has no third-party dependencies. A browser, website checkout, database
service, and cloud account are unnecessary for running experiments.

```text
settlers/
  research/   policies, experiments, results, and this guide
  server/     authoritative game server and Rust search players
```

## 1. Build the server and search players

Run these commands from `research/`:

```sh
just setup
just tables
```

`setup` builds the release server and its remote policy runner, including the
expectimax searches. `tables` unpacks and verifies the committed learned tables
used by **`ntuple-leaf`, the current protocol baseline**. No model download or
training run is needed. If the server checkout is elsewhere, set
`SETTLERS_SERVER_DIR=/absolute/path/to/server` before running these commands.

## 2. Keep the server running

```sh
just server
```

Leave this terminal open. The server listens at `http://127.0.0.1:5555` and keeps
its local state, event archive, and signing key in `.runtime/server/`. Restarting
it with the same directory preserves games and identities.

## 3. Play a first game

Open a second terminal in `research/`:

```sh
just doctor
just match ntuple-leaf expectimax-v2-plan ntuple-leaf expectimax-v2-plan --games 1
```

The doctor prints the server's health and protocol version. The match command
prints an experiment ID, a run ID, then the game result. It plays a real ten-point
game with four independent search processes. This [smoke run](concepts.md#smoke-run) checks your setup; it does not compare
policy strength.

For one full rotation through the seats, use the same command with `--games 4`.
Next, [build your own client](client.mdx) and register a longer simulation.

## Choose the table you need

| Table | Command | Use |
| --- | --- | --- |
| Current search players | `just match ntuple-leaf expectimax-v2-plan ntuple-leaf expectimax-v2-plan --games 4` | Develop against learned and hand-written search leaves |
| Historical evaluation lineup | `just match ntuple-leaf expectimax-v2-plan eta fast --games 4` | Reproduce the policy mix used when the learned leaf became the baseline |
| Simple builders | `just match fast eta fast eta --games 4` | Check a cheaper baseline or behavior against builders |
| Python adapter | `just match legal-first ntuple-leaf expectimax-v2-plan ntuple-leaf --games 1` | Check a custom-client starting point |

`ntuple-leaf` uses expectimax with learned position values. `expectimax-v2-plan`
uses the same frozen depth-3 search with a hand-written leaf. Both have a 1.5 s
search budget per decision. `fast` and `eta` are simpler Rust builders, included
by `just setup`. The [opponent guide](play-policies.md) lists the other choices.

<AgentContext>

## Connection settings

| Setting | Default | When to change it |
| --- | --- | --- |
| `SETTLERS_SERVER_DIR` | Sibling `../server` | Server source is elsewhere |
| `SETTLERS_BIND` | `127.0.0.1:5555` | A second local server needs another port |
| `SETTLERS_SERVER_URL` | `http://127.0.0.1:5555` | The harness should connect to another address |

The server bind address and the client's URL are separate. For example:

```sh
# Server terminal, from research/
SETTLERS_BIND=127.0.0.1:5556 just server
```

```sh
# Client terminal, from research/
export SETTLERS_SERVER_URL=http://127.0.0.1:5556
just doctor
```

Stop the previous server before reusing its storage. Two simultaneous servers
need separate research runtime directories as well as different ports.
`just server` uses port 5555; starting the server directly from its own repository
defaults to port 8080.

## If the first game does not start

| Symptom | Next step |
| --- | --- |
| Connection refused | Keep `just server` running and check `SETTLERS_SERVER_URL` |
| Missing `server` or `remote` executable | Run `just setup` with the correct `SETTLERS_SERVER_DIR` |
| Missing learned tables | Run `just tables` from `research/` |
| Policy exits or never becomes ready | Read `runs/RUN_UUID/match-0000/private/policy-SEAT.log` |
| Match or decision deadline exceeded | Inspect the retained result; lower concurrency before trying a fresh run |

A failed match stops the schedule and remains in the result. `Ctrl-C` stops the
owned policy processes and records an interruption; the server retains the game.
Its later timeout actions do not become completed evidence for that run.

## Optional offline development

The [engine arena](concepts.md#engine-arena) runs games without HTTP or WebSockets and uses the same two
repositories. It accepts built-in Rust seat specifications, not arbitrary stdio
clients. Use it for search development; verify a frozen candidate through the
server before changing the protocol baseline.

```sh
just build-arena
just study log/search-development --title 'Local search development' \
  --question 'Which search configuration should advance to a protocol comparison?'
just engine-register --study log/search-development \
  --seats v2 v2 v2 v2 --seeds 0-3 --deterministic \
  --hypothesis 'This fixed configuration completes a development smoke.' \
  --decision-rule 'All games must complete; make no strength claim.'
just engine-run EXPERIMENT_ID
```

`v2` is the default hand-written search, not the registered `ntuple-leaf` alias.
See `server/docs/expectimax.md` for Rust configurations and learned-table paths,
and the [experiment program](experiment-program.md) for the two evidence tiers.

</AgentContext>
