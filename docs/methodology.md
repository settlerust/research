# How to compare policies

The basic unit is a complete game. A lineup contains two to four **competitor
slots**. Slots remain distinct when the same policy appears more than once;
otherwise one could accidentally count three identical opponents as three
independent games. Run `N` games in multiples of the player count for equal seat
exposure. Match `i` rotates slot assignments by `i` seats. The server independently
chooses the opening player and game randomness.

The current public API does not accept a seed. Record game IDs, rules, source and
binary hashes, and the public event history. These support auditing the recorded
game; rerunning the same lineup does not reproduce its random stream. Describe
comparisons as **unpaired**. Paired-seed evaluation needs a separately designed
server/offline interface that still hides randomness from policies.

## Before a run

Register a mechanism, falsification criterion, fixed opponents, game count,
wall-clock and turn caps, decision budget, and stopping rule in `experiments/`.
Keep development and fresh evaluation cohorts separate. Freeze the candidate
before the fresh run. Do not tune against the cohort used for a final claim.
Record the environment for timing comparisons; network/storage latency is part
of this arena and is not engine throughput.

## Outcomes and uncertainty

Report planned, attempted, completed, incomplete, and unplayed counts. Wins,
losses, win rate, and mean points use **completed valid games** only. The harness
labels server timeout moves invalid even when a winner is declared. Decision or
match budget exhaustion is censored. Invalid actions and process failure are
invalid. An operator interruption is recorded. Any non-completed game stops the
remaining schedule; do not silently refill it with favorable replacements.

The printed 95% Wilson interval is descriptive for each competitor slot over
completed games. Slots within a game are dependent. For policy contrasts, retain
whole-game rows and use a game-level analysis; do not pool duplicated seats as
independent trials. Completion-conditioned rates may be biased if censoring
depends on strategy. Publish the censor rate and reason with any comparison.

Also inspect turn count, final points, public event counts (builds, trades,
production, robber actions, discards, timeouts), and runtime. Stdio decision
latency is measured; native process decision latency is not observed separately.
The raw public tapes support richer analyses without accessing private hands.

## Durable evidence

Each run first writes a manifest and frozen experiment copy. It records research
source hashes, available local binary hashes, Git state, settings, and the planned
schedule. An available local server binary hash is a provenance hint, not proof
of what a remotely hosted server is running. For remote studies, obtain and retain
the server operator's build identity separately.

The final inventory hashes every public artifact. `records/runs/` retains one
compact Markdown summary per run, including failed preflight. `just archive`
verifies those hashes and creates an exclusive bundle plus a receipt. Bulk data
is ignored by Git. A run is only locally durable until a verified copy exists on
the intended durable storage. Record an immutable URL and digest after an
authorized upload; no cloud destination is preconfigured.
