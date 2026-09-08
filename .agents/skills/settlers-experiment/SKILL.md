---
name: settlers-experiment
description: Register, implement, and run headless Settlers policy experiments with durable evidence. Use for strategy research or protocol policy comparisons in this repository.
---

Read `docs/status.md`, `docs/methodology.md`, and the relevant approach before
choosing an experiment. Read `docs/protocol.md` when adding a policy.

Use `just policies` to inspect opponents and `just doctor` to check the server.
The default endpoint is `http://127.0.0.1:5555`. `just setup` builds a separate
server checkout selected by `SETTLERS_SERVER_DIR`; `just server` runs it in the
foreground with research-owned local storage. An existing remote endpoint can
be selected with `SETTLERS_SERVER_URL`.

Register the hypothesis and decision rule using `python3 -m harness.cli register`
with `--players`, `--games`, `--hypothesis`, and `--decision-rule`. Use a game count
divisible by the player count for balanced seat exposure. Edit budgets only
before first execution. `just run EXPERIMENT_ID` uses that immutable protocol.
For an implementation smoke check use `just match fast eta legal-first eta`.

Implement strategies under `policies/` and register an argv array in
`policies/registry.toml`. Stdio processes receive their own complete observation,
topology, and newly delivered participant events, then emit one protocol Command
or null. Keep memory in the process; flush stdout. Native remote processes own
their socket and must reuse the supplied seat token. Each process receives a
separate identity; hidden data and other players' credentials are not inputs.

Run `just check` and a cheap protocol smoke match before a larger study. Inspect
validity and completion before interpreting a win rate. Do not count incomplete
games as losses, pool repeated policy slots as independent games, or claim paired
seeds: the public server controls and hides randomness. Stop when a match fails;
diagnose it before registering a new run.

Every run writes a manifest, per-game artifacts, a final hash inventory, and one
Markdown record. `just archive RUN_UUID DESTINATION` makes a verified immutable
bundle without credentials. Preserve a truthful receipt: local copies are not
remote backups. Append the daily log after interpreting evidence, including
negative results and actual contributor attribution. For reports and exhibits,
use the sibling `settlers-publishing` skill.
