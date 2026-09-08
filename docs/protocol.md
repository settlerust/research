# Writing a policy

All policies ultimately read `GameView` and write the server's `Command` JSON
schema. The authoritative documentation and schemas are served at `/v1/schema`
and `/v1/topology` with authentication; a server checkout also includes
`docs/api.md` and `docs/protocol.schema.json`. Protocol version is currently 1.

## Stdio adapters

Add an entry in `policies/registry.toml` with `transport = "stdio"` and an argv
array. Commands run from the research root. Supported placeholders are
`{python}`, `{root}`, `{server}`, `{base}`, `{game}`, `{token_file}`, and `{name}`.
Never interpolate shell command strings. Compile Rust or TypeScript policies
before registering a run; point the command at the resulting executable.

The harness starts one persistent process per seat. Each line on stdin is:

```json
{"protocol":1,"view":{"id":"…","version":8,"game":{}},"topology":{},"events":[]}
```

The abbreviated objects above are complete typed protocol data at runtime.
Return one JSON line containing a `Command`, or `null` if there is no action:

```json
{"type":"act","action":{"type":"roll"}}
```

Flush stdout after every response; send diagnostics to stderr. Responses have a
16 KiB limit and a preregistered decision deadline. `policies/legal_first.py` is a
working example. The process retains its own memory across decisions. `events`
contains newly delivered batches for that participant, including directed
communications it may see. Empty redacted batches still advance the independent
history cursor. A snapshot version is not an event cursor.

The harness owns each seat's authenticated REST client, snapshots, envelope UUID,
expected version, and retries. A transport ambiguity retries the same entire
envelope. A conflict fetches fresh state and asks the policy again. Only the
server determines legality, trades, random draws, and the winner. `legal_actions`
contains useful finite actions but is not exhaustive for all discard/trade
quantities. Policies may emit other legal commands.

## Independent network processes

`transport = "remote"` starts a process that owns its HTTP/WebSocket connection.
The harness prejoins the seat and writes its token to the supplied private token
file. The process must reuse that identity, connect its WebSocket (so readiness
is visible), wait for start, and exit after a terminal state. Each player has a
distinct token. The existing `fast` and `eta` Rust runners implement this contract.

Remote policies can act simultaneously; the server resolves ordering. Stdio
decisions are scheduled sequentially by seat. Record this transport difference
when studying negotiation timing or fairness. Native runtime stderr and all
credentials stay in ignored private directories and never enter public archives.

## Public replay encoding

Topology uses integer pointy-hex coordinates. Scale x by sqrt(3) relative to y
to draw regular hexagons. A hex byte stores its dice total in the high nibble and
terrain in the low nibble: 0 desert, then brick/lumber/wool/grain/ore as 1–5.
Buildings use 0 empty, 1–4 settlements, 5–8 cities; owner is `(value - 1) % 4`.
Road values are null or seat index. Player points are public midgame; the server
reveals final scoring at the terminal state.
