---
title: Research experiment program
summary: How to register a study, compare policies fairly, report uncertainty, and retain reproducible evidence.
---

# Research experiment program

These are draft study designs. They are not registered experiments, implemented candidate policies, scheduled runs, or measured results. Each approach page specifies its mechanism, treatment arms, diagnostics, and failure conditions. This document supplies the shared design needed to make a comparison interpretable.

The [experiment log](../log/experiments.mdx) tracks investigations and findings.
Use the [research workflow](research-workflow.md) to give each registration an
owning approach or cross-cutting study and keep its documentation current.

## From a question to a comparison

The [Roadmap](roadmap.md) walks through the open research. This page is the shared procedure for testing any of those questions.

## Research sequence

| Stage | Question | Candidate studies | Exhibit to retain | Gate before proceeding |
| --- | --- | --- | --- | --- |
| 0 · Measurement | Can decisions and outcomes be reconstructed fairly? | Fixed fast/ETA reference; candidate-score and message trace audit | Completion chart, public replay, reference-versus-selected table | Legal actions, redaction, complete records, working fallbacks |
| 1 · The island | Does better resource conversion beat a productive but rigid plan? | Opening, tempo, expansion, ports | Build-time curves, resource bottleneck plot, route replay | Frozen baseline and reliable event diagnostics |
| 2 · Uncertainty | Do calibrated beliefs improve decisions at equal cost? | Beliefs, search, risk, development | Reliability curve, latency frontier, outcome distribution | Held-out calibration, no hidden-state leakage |
| 3 · Conversation | What changes when an offer gets a message? | Bargaining, signals, disclosure | Offer-response timeline and bilateral value scatter | Same action offers, message limits, response windows |
| 4 · Social continuation | When do concessions recover their cost? | Reputation, pliability, containment | Concession trajectory and win-versus-cost frontier | Fixed reference, identifiable recipient memory, eligible alternatives |
| 5 · Generalization | Does the gain survive unfamiliar tables? | Adaptation, population, crossed ablations | Full-lineup heatmap with denominators and intervals | Frozen checkpoints and fresh opponent mixtures |

The stages describe dependencies, not an automatic job queue. A useful early pair is a build-tempo improvement and a message-only comparison with unchanged offers. Avoid combining deeper search, a new language model, new memory, and new objectives in the same first candidate.

## A concrete default study envelope

Use this as a starting draft, then adjust and register it before any evidence collection. The sample count is a planning budget, not a claim of statistical power.

| Field | Draft default |
| --- | --- |
| Rules | Four players, normal ten-point game; freeze the exact server rules and build identity |
| Unit assigned | Whole game; one focal treatment slot, three frozen opponent slots |
| Lineups | Three predefined tables; each arm sees each exact lineup equally |
| Development cohort | 24 games per arm total, balanced across seats and lineups; diagnostics and tuning only |
| Fresh evaluation cohort | 240 games per arm total: 80 for each of three fixed tables, with equal focal-seat exposure |
| Decision deadline | 2 seconds per action including any model call, using a preregistered legal fallback |
| Game cap | 30 minutes and 500 turns; reaching either cap is incomplete evidence |
| Message allowance | At most one public message per own turn; freeze length, delivery timing, recipients, and response window |
| Primary outcome | Completed-valid-game win-rate difference for one named candidate-versus-reference contrast |
| Completeness | Report planned, attempted, valid completed, incomplete, invalid, and unplayed games for each arm |
| Stop rule | Stop the run on the first failed or incomplete match; investigate and record before registering a new run |

The existing harness supports the base policy protocol, per-game records, budgets, and seat rotation. It does not yet implement every proposed message treatment, persistent tournament identity, belief diagnostic, or research candidate. Those capabilities must pass stage 0 before a study that depends on them. Match the concrete field names and executable argv to the harness and policy implementation at registration time.

Choose the minimum effect worth detecting before the fresh cohort. Estimate an appropriate sample size using development data and a predeclared power or precision calculation. Increase the draft budget before starting if needed. Do not run to an arbitrary favorable significance threshold.

## Freeze the opponents, not just their names

For the first mechanical study, use the available fixed `fast` and `eta` versions. Retain competitor slots separately when a policy appears more than once. For social studies, first implement and verify these behavioral controls:

| Opponent class | Controlled behavior | What it tests |
| --- | --- | --- |
| Silent builder | Responds only through a frozen action policy; ignores chat | Whether language gains require a responsive recipient |
| Reciprocal trader | Changes later acceptance using recipient-specific observed history | Whether concessions can be repaid |
| Skeptical trader | Discounts unsupported messages while considering useful offers | Whether effects survive distrust |
| Opportunist | Accepts favorable deals without promising reciprocity | Vulnerability to exploitation |
| Adaptive negotiator | Updates behavior from interactions under a fixed rule | Generalization to a changing response policy |

A class label is insufficient for a preregistration. Record exact policy/model versions, settings, prompts, memory reset rules, and the complete three-opponent tuple. Social effects involve interference: changing the focal player changes the other players’ later states. Analyze that as part of the whole-game policy effect.

## Separate the mechanisms

For the central question about pliability, compare these arms in sequence:

1. **Fixed reference.** Choose the highest unchanged expectimax value.
2. **Belief update.** Use conversation to predict opponent behavior, with unchanged preferences and no concession term.
3. **Social continuation.** Add an explicit estimate of future response to the evaluator, avoiding double-counted value.
4. **Bounded reranking.** Keep the reference fixed and let social context choose within a declared foregone-value cap.
5. **Unbounded reranking.** A diagnostic arm to reveal the cost and benefit of removing that cap.

Run message/no-message and memory/no-memory ablations after the core contrast. A small factorial study can test interactions between truthfulness, memory, and cap size, but nominate one primary contrast and correct or clearly label exploratory comparisons. Persona labels alone are not independent experimental variables.

The current selective-model eligibility threshold decides whether to ask for an intervention. It is not an enforced cap on the chosen candidate’s foregone value. Implement the latter explicitly before claiming to test bounded pliability.

## Decision traces and outcomes

Every decision should retain observation version, legal candidate IDs, fixed reference values and units, selected action, applied action, recipient-visible context extent, and timing. For social decisions also record the claim category, literal statement, estimated response, social value component, cap, and fallback reason. Do not expose private notes in public exhibits.

Primary strength analysis uses whole games. Trade acceptance, calibration, opponent targeting, timing, cumulative foregone value, and reputation proxies explain possible mechanisms. They are not substitutes for wins. Log available opportunities: zero reciprocation when no future trade was possible differs from repeated refusal.

For a policy contrast use an unpaired game-level analysis, retaining the full within-game outcome vector. Resample whole games, stratified by lineup, or use a preregistered game-level model; do not resample turns or repeated policy seats as independent observations. Persistent-memory studies require session or group clusters and randomized reset conditions. The public API supplies no paired seeds.

## What counts as support

Before running, name a minimum meaningful win-rate gain, an acceptable completion rate, maximum added cost, and one primary contrast. Report the effect with uncertainty and the complete denominators. A draft decision rule is: support the candidate only if the preregistered interval excludes no improvement, the estimated gain reaches the meaningful threshold, and the completion/cost constraints hold. An interval overlapping zero is inconclusive; it is not proof of equivalence.

A failed mechanism prediction remains a useful result even when the primary comparison is inconclusive. Retain adverse matchups, expensive fallbacks, and negative findings. Do not change a completed experiment, quietly refill censored games, or promote a smoke test into strategic evidence.

## From proposal to registered experiment

Implement one bounded candidate in an isolated branch or worktree. Run protocol and information-boundary checks, then a small smoke match. Register the final executable lineup, hypothesis, counts, budgets, and decision rule with the harness. Run development and fresh evaluation as separate registrations. Archive retained evidence before writing a claim.

File the study before registering with `--study OWNER/SLUG`; temporary worktrees
belong inside `.worktrees/`. See [the protocol](protocol.md),
[publishing](visual-publishing.mdx), and [research organization](research-workflow.md).
Keep these proposal pages alongside later findings so a reader can compare the
original hypothesis with what the experiment actually showed.


## Two evidence tiers

Evidence comes from two arenas, and every result names its tier.

| Tier | Where games are played | Randomness | Use |
| --- | --- | --- | --- |
| Engine arena | Offline, in the server's `crates/arena` process; seats receive `observe()` and participant events only | Explicit seeds; every seed is played once per lineup rotation, so lineups are compared on identical boards | Development, tuning sweeps, tree-structure measurements, and screening comparisons |
| Protocol arena | Independent processes against the authoritative HTTP server | Server-generated and hidden by default; a deterministic research table may pin a seed index, still hidden from seats | Confirmation of a frozen candidate, protocol compatibility, latency under transport |

Engine-arena runs register with `just engine-register --study OWNER/SLUG --seats ... --seeds A-B`
and execute with `just engine-run EXPERIMENT`. Their run records say "Tier: engine
arena". Paired seeds make the seed-level win difference between two slots a
natural contrast; the record reports its mean and a normal-approximation
interval over seeds. A candidate frozen after engine-arena development still
needs a fresh protocol-arena cohort before the evidence boundary changes.
Exploratory sweeps that guide tuning are not registered; the daily log names
them as unregistered and they carry no evidential weight.

## Compare policies fairly

The basic unit is a complete game. A lineup contains two to four **competitor
slots**. Slots remain distinct when the same policy appears more than once;
otherwise one could accidentally count three identical opponents as three
independent games. Run `N` games in multiples of the player count for equal seat
exposure. Match `i` rotates slot assignments by `i` seats. The server independently
chooses the opening player and game randomness.

By default the server draws its own seed and every random event advances one
shared stream, so rerunning a lineup does not reproduce its luck and such
comparisons are **unpaired**. Deterministic mode changes that: with
`settings.deterministic` the k-th roll, k-th theft, and k-th development draw are
read from seed-derived tapes indexed by count, and an agent-only research table
may pin its seed index at creation. Register such a cohort with
`just register --seeds A-B`; each seed is then played once per lineup rotation,
the run record reports the paired seed contrast, and seats still never receive
the seed or the tape. Ordinary and browser games keep the shared stream. Record
game IDs, rules, source and binary hashes, and the public event history in both
modes.

### Before a run

Register a mechanism, falsification criterion, fixed opponents, game count,
wall-clock and turn caps, decision budget, and stopping rule in `experiments/`.
Keep development and fresh evaluation cohorts separate. Freeze the candidate
before the fresh run. Do not tune against the cohort used for a final claim.
Record the environment for timing comparisons; network/storage latency is part
of this arena and is not engine throughput.

### Outcomes and uncertainty

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

### Durable evidence

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


### First executable ablation

The [liquidity study](../reports/liquidity-baseline.mdx) compares two target-time
estimators inside one shared Rust implementation and transport. Its
[audit trail](../reports/liquidity-audit.md) records protocol compatibility failures,
a stopped evaluation and a separately registered fresh cohort. A smoke or failed
build must not silently become the candidate's evaluation.

Configured research-owned executable hashes and Cargo.lock are now retained in
run manifests; generated target directories are excluded from source snapshots.
Current public event tapes omit research-only theft details and directed chat.
Earlier immutable tapes predate that filter, as disclosed in the audit.
