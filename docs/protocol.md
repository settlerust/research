---
title: Client protocol reference
summary: The observation and command contract, persistent stdio adapters, event cursors, and independent network clients.
---

# Client protocol reference

A policy reads its own `GameView` and emits a server `Command`. Start with the
[working Python client](client.mdx); use this reference when extending its
behavior or connecting directly over the network.

## The stdio contract

The harness starts one persistent process per seat, working from `research/`.
Each input line has this shape; the nested objects are abbreviated here:

```json
{"protocol":1,"view":{"id":"…","version":8,"game":{}},"topology":{},"events":[]}
```

Return one JSON line containing a command, or `null` when there is nothing to do:

```json
{"type":"act","action":{"type":"roll"}}
```

| Field or behavior | Contract |
| --- | --- |
| `view` | This participant's current observation, including its own hand and public game state |
| `topology` | Board coordinates and hex, vertex, edge, and port connections |
| `events` | Newly delivered batches filtered for this participant, including directed messages it may see |
| stdout | One JSON response per input line, flushed, at most 16 KiB |
| stderr | Diagnostic output retained privately |
| Memory | The process survives decisions within one game; a new game starts a new process |
| Deadline | Five seconds by default for stdio input and response; fixed in the experiment |

`legal_actions` offers useful finite actions but is not exhaustive for arbitrary
trade quantities or discards. A policy may emit other legal commands. The server
validates legality and remains responsible for rules, randomness, and scoring.

## Register an executable

```toml
[my-agent]
transport = "stdio"
command = ["{python}", "policies/my_agent.py"]
description = "My observation-driven player"
```

Commands are argv arrays, never shell strings. Supported placeholders are
`{python}`, `{root}`, `{server}`, `{base}`, `{game}`, `{token_file}`, and `{name}`.
Compile a Rust or TypeScript policy before running; point the registry to its
executable. Double literal braces in JSON command arguments, as the frozen
search entries in `policies/registry.toml` do.

## What the harness handles

| Responsibility | Behavior |
| --- | --- |
| Identities | Creates the table and prejoins every policy with a distinct credential |
| Readiness | Keeps a WebSocket connected for each stdio seat and marks it ready before the host starts |
| Requests | Submits commands with an expected snapshot version and request UUID |
| Ambiguous delivery | Retries the exact same envelope, preserving request identity |
| Version conflicts | Fetches fresh state and asks the policy again |
| History | Advances a separate cursor for each participant and delivers its filtered events |
| Evidence | Retains public spectator frames, event tapes, results, source snapshots, and digests |

A snapshot version is not an event cursor. Empty redacted batches still advance
history. The stdio presence connection drains WebSocket frames; observations
and participant history still arrive through REST. A lost presence connection
invalidates the run, preserving the failure instead of silently continuing.
Never feed spectator replays, another seat's hand, or server archives into a player policy.

<AgentContext title="Direct network clients and wire details">

## Own the HTTP and WebSocket connection

`transport = "remote"` starts a process that owns its network connection. The
harness has already joined its seat and written its token to the supplied
private token file. Reuse that identity, connect the WebSocket so the seat is
reported as connected, wait for start, and exit after a terminal state.

The `server` checkout includes Python, TypeScript, and Rust clients under
`clients/`, with examples in `docs/clients.md`. Its
`crates/policies/src/bin/remote.rs` runner implements this contract for the
builders and expectimax searches.

Remote processes can act concurrently; stdio decisions are scheduled
sequentially by seat. Keep this difference fixed when studying negotiation
timing or fairness. Remote search budgets come from their configured policy;
the harness's stdio decision deadline does not control their computation.

A direct client owns pending envelopes, token renewal, reconnect, and recovery
from its last event cursor. The complete lifecycle and retry rules are in
`server/docs/api.md`. The authoritative schemas live in
`server/docs/protocol.schema.json`; an authenticated client can also request
`/v1/schema` and `/v1/topology` from the server. Protocol version is currently 1.

## Board encoding

| Data | Encoding |
| --- | --- |
| Hex coordinates | Integer pointy-hex topology; scale x by √3 relative to y for regular hexagons |
| Hex byte | High nibble: dice total; low nibble: terrain |
| Terrain | 0 desert, then brick, lumber, wool, grain, ore as 1–5 |
| Buildings | 0 empty, 1–4 settlements, 5–8 cities; owner is `(value - 1) % 4` |
| Roads | `null` or seat index |
| Points | Public points midgame; final scoring is revealed at the terminal state |

Use the [registered replay component](publishing.md#flat-replay) when publishing
a game, so the notebook keeps one shared rendering of the board.

</AgentContext>
