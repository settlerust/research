---
title: Current evidence
summary: The ntuple-leaf baseline, the next protocol candidate, and the limits of the research so far.
---

# Current evidence

Use **`ntuple-leaf`** as the reference for a new candidate. It is the latest
policy to meet its registered rule through the authoritative server. Engine
experiments pointed to a quarter-strength blend as the next candidate; its
protocol pair on twenty boards was inconclusive, so the reference is unchanged.

## LLMs against Expert

The [LLM arena competition](../reports/llm-arena.mdx) completed all ten registered
games: GLM won six, DeepSeek two, Kimi one and learned expectimax one. GLM won
a majority; GLM and DeepSeek meet the registered descriptive rule of winning
more than Expert. Expert still had a better average finish and score than
DeepSeek. Wide win-rate intervals, uneven deadline/provider failures and unequal
input modalities limit a general strength claim. The LLMs also received learned
search advice, so this is not a comparison of unaided LLMs with search.

The [final audit](../records/runs/63ac76cc-e098-4974-8b2f-61a5d3d85be5.md)
retains every game and failure. The earlier Inkling comparison and two
intentionally interrupted JSON-input games remain separately archived. The
established protocol baseline below is unchanged.

## The protocol baseline

With the same depth-3 search and 1.5-second budget, the learned leaf won
<WinRate value="46" total="80" label="ntuple-leaf" /> against
<WinRate value="25" total="80" label="expectimax-v2-plan" />.
All 80 games on 20 deterministic seeds completed validly without timeout moves.
The paired effect was <ResultComparison value="0.263" low="0.094" high="0.431" />.

<ResearchChart asset="ntuple-leaf-protocol-wins" />

This established the baseline for one lineup and one rotation scheme. It does
not establish strength against humans or every opponent population. The
[protocol report](../reports/ntuple-leaf-protocol.mdx) includes the registration,
complete denominator, and public replay.

## The next candidate, through the protocol

The [quarter-strength blend](../reports/leaf-blend.mdx) adds a small contribution
from the hand-written evaluator to the learned tables. Its effect survives both
engine lineups: builders and a table with three searches.

<ResearchPlot asset="leaf-blend-pooled-effects" />

The after-the-fact pools cover 192 builder boards and 128 population boards.
Decision time rises by about 40%. Through the protocol arena, as a swapped
pair on twenty deterministic boards inside `ntuple-leaf`'s exact search
([report](../reports/blend-protocol.mdx)), the blend won
<WinRate value="34" total="80" label="blend, half A" /> and
<WinRate value="34" total="80" label="blend, half B" /> against
<WinRate value="33" total="80" label="ntuple-leaf, half A" /> and
<WinRate value="32" total="80" label="ntuple-leaf, half B" />, a
seating-corrected effect of <ResultComparison value="0.019" low="-0.087" high="0.124" />.
That is inconclusive by the registered rule and covers both zero and the engine
estimate; under the 1.5 s clock on a loaded machine the blend completed depth 3
in about 51% of contested decisions against 61% for the tables alone. The server
default stays `ntuple-leaf`; resolving an effect of the engine's size would take
a pair of about 64-board halves. The browser still uses the hand-written leaf;
these table-based results do not transfer directly to it.

## What the other comparisons changed

| Result | Decision |
| --- | --- |
| [Deeper learned-leaf search](../reports/ntuple-leaf.mdx): 27 wins against 43 in the protocol cohort | Keep the shallower baseline |
| [Transposition cache](../reports/transpositions.mdx): identical moves in 11.7% less time at equal nodes | Treat it as a computation saving; the protocol strength interval crosses zero |
| [Search-switch retest](../reports/tables-retest.mdx): 145 swapped pairs, 74,240 games | Keep bargaining, eight dice scenarios, and four sampled worlds; the other tactical switches do not justify a default change |
| [Seating diagnosis](../reports/arena-seating.mdx): identical adjacent searches can differ | Measure two-search comparisons in both seatings; rotating seats alone preserves adjacency |

The [experiment timeline](../log/experiments.mdx) links the individual studies.
The [client guide](/research/client) explains how to implement and run a candidate,
and the [experiment program](experiment-program.md) explains how to measure it.

<AgentContext title="Earlier comparisons and complete evidence history">

The entries below preserve the sequence of findings. Statements about a new or
retained baseline describe that point in the research history; the current
reference is `ntuple-leaf` as stated above.

This repository starts with a headless protocol harness, existing Rust fast/ETA
opponents, and a minimal Python policy adapter. Setup and smoke validation do
not establish a strategy ranking. No claim of optimal play has been made.

Consult `records/runs/` for actual run outcomes and `reports/` for selected
publications. Promote a finding here only when a fixed candidate, retained
artifacts, complete denominators, and the stated decision rule support it.

The [strategy atlas](../approaches/README.md) now defines sixteen proposed directions, with animated mechanisms, study briefs, and a shared [experiment program](experiment-program.md). No new strategy evaluation was run to create this guide. Interactive teaching values and synthetic publishing fixtures remain explicitly separate from recorded evidence.


## First strategy comparison: retain ETA

The [liquidity experiment](../reports/liquidity-baseline.mdx) completed all 80
registered evaluation games in [80-game protocol cohort](/research/records/runs/de39917c-55da-40ad-a53a-5b8588898810).
Liquidity won 20/80 (25%); ETA control won 26/80 (32.5%). The observed contrast
was −7.5 percentage points and the preregistered improvement rule failed.
ETA remains the baseline; the result does not prove inherent inferiority or
establish general strength across opponent populations.

The candidate changes only the target acquisition-time estimator, with shared
protocol adaptations and a 16-offer budget across all policies. Both native
policies and the comparator source are retained under `policies/liquidity/`.
The [audit](../reports/liquidity-audit.md) preserves the startup failures, rate-limit
failure, stopped first evaluation and all smoke runs. None was pooled into the
fresh cohort. All archives are verified local copies.

## Engine arena and the tunable search

An offline engine arena now plays paired-seed games with only redacted
observations reaching each seat. Its [calibration](../reports/engine-arena-calibration.mdx)
reproduces the protocol ordering of the two builders over 512 slot-games and
shows the frozen `expectimax-v1` reference losing to both (13.3% against 30.1%).
Engine-arena results are development-tier evidence; they do not replace a
protocol cohort.

`expectimax-v2`, a tunable turn-level search with an acquisition-time leaf,
won 34.0% of 256 paired slot-games against ETA's 24.2% at depth 2 (paired
contrast +0.098, 95% interval +0.005 to +0.190). See the
[development report](../reports/expectimax-v2-development.mdx). The frozen
depth-3 candidate then won 38.8% of an 80-game protocol cohort against the
compared ETA slot's 31.2%, short of its registered rule, so the protocol-arena
baseline remains ETA and that candidate's advantage is not confirmed.

Those cohorts ran with a turn-planning defect. After the
[correction](../reports/expectimax-v2-corrected.mdx), depth 2 wins 50.4% of 256
paired slot-games against ETA's 20.3% (paired contrast +0.301) and depth 3
under 1.5 s wins 57.4% (contrast +0.414).

## Deterministic mode and ablations

Both tiers can now play deterministic paired cohorts: the k-th roll, theft, and
development draw come from seed-derived tapes, so two policies on one seed face
identical luck. A protocol smoke confirmed identical rolls across rotations
through the server. An [ablation program](../reports/ablations.mdx) of eighteen registered
cohorts (one change per arm against an unchanged depth-2 control, 256
deterministic games each) found two decisive levers, lookahead (−0.324 wins
per game when removed) and dice scenarios (−0.410 with two instead of eight),
and no single leaf term or style slider worth more than 0.1 wins per game on 64
seeds. On 192 fresh seeds one belief mechanism held up: sampling hidden hands from
the event history rather than public counts alone is worth about 0.07 wins per
game; the expansion terms, sampled-world count, trade margin, and plan term
showed no measurable effect at depth 2.

## Two searches at one table

The one-change arm design seats the changed search in slot 0 and the control in
slot 1, and slot 1 always sits one seat after slot 0. That order matters: two
identical default searches differ by +0.176 wins per game (95% interval
+0.083 to +0.268) on boards 0 to 63 ([256-game engine cohort](/research/records/runs/91ddb42d-82ab-460b-95c2-b8d340658369)) and by +0.051 (−0.046 to
+0.148) on boards 64 to 127 ([256-game engine cohort](/research/records/runs/9d213ed0-a04f-442b-8d89-1dd3fdd99ab1)). The cause is the game's turn
order, not the arena's trade handling: the seat directly before another acts
first after three of the four rolls in a round, the term survives every trade
switch and identical builders, and it disappears with a builder between the
two searches ([seating report](../reports/arena-seating.mdx)). The
[bargaining arms report](../reports/bargaining-arms.mdx) reads its arms against
the first null and confirms the counters effect with a swapped pair on fresh
boards, −0.096 (−0.156 to −0.035) for the seat without counters. Any contrast
between two searches at one table must be measured in both seatings before it
counts as evidence; the +0.219 for threat-aware bargaining over plain
acceptance ([256-game engine cohort](/research/records/runs/4228f4f7-4427-42a4-8c0f-3976e1d26c76)) is withdrawn as a strength claim, corrected
estimate +0.043 (−0.082 to +0.168) on the same boards.

The build-prediction [study](../reports/build-prediction.mdx) corroborates the
seating term with a different lineup: two identical depth-2 searches with ETA
and fast split +0.172 wins per game (95% interval +0.083 to +0.261) for slot 0
on seeds 0 to 63, and evenly on seeds 64 to 79. The single-order ablation
cohorts on the development seeds therefore lean positive by about that much,
and their near-zero arms may be slightly negative. That study ran its three
prediction switches as mirrored pairs in both seatings; none was confirmed on
fresh seeds.

## A learned leaf beats the hand-written leaf

Lookup tables of hex and portfolio patterns, learned by self-play in under two
hours (`patterns/ntuple-leaf`, [report](../reports/ntuple-leaf.mdx)), replace
the leaf of `expectimax-v2` with nothing else changed. On 64 fresh deterministic
boards the tables at depth 2 won 130 of 256 slot-games against 74 for the
hand-written leaf in the same search (paired contrast +0.219, 95% interval
+0.124 to +0.314); played one ply they beat the two-turn hand-written search,
at depth 2 they beat the hand-written leaf at depth 3, and at depth 3 against
depth 3 the margin is +0.242. This is engine-arena evidence on one lineup with
two fixed builders; the tables are a server-side policy (`ntuple-leaf`) and the
browser keeps the hand-written leaf.

## The protocol-arena baseline is now ntuple-leaf

Through the authoritative server, `ntuple-leaf` (the `expectimax-v2-plan`
search with the learned tables as its leaf) [won 46 of 80
games](../reports/ntuple-leaf-protocol.mdx) against 25 for `expectimax-v2-plan`
on 20 deterministic seeds played once per rotation, a paired contrast of +0.263
wins per game (95% interval +0.094 to +0.431), all games valid. The registered
rule is met. New candidates should be compared against `ntuple-leaf` in a
four-player table with the fixed builders. As before, the comparison is one
lineup and one seat rotation scheme; strength against other searches, humans,
or negotiation-aware opponents is not established.

A deeper configuration of the same player, `ntuple-leaf-deep` (depth cap 4
under a 4 s budget with decision-aware deepening), [lost its protocol
cohort](../reports/ntuple-leaf.mdx) against `ntuple-leaf` 27 to 43 (paired
contrast −0.200, 95% interval −0.357 to −0.043), so it is not the baseline.

The search's transposition tables were rebuilt with a verified key and a
per-decision or per-turn lifetime ([report](../reports/transpositions.mdx)):
identical decisions from 11.7% less time at equal nodes, and no strength
change at equal time or through the protocol (27 to 36, interval crossing
zero), so `ntuple-leaf` remains the baseline and the tables are a cost saving.

## Every search switch under the learned leaf

Nine engine-arena studies retested the search's switches with the learned
tables as the leaf, as seating-corrected swapped pairs at a table of builders
and a table of three searches (145 pairs, 74,240 games; [synthesis](../reports/tables-retest.mdx)).
Bargaining and the search's information inputs hold; the one improvement is the
hand-written terms blended into the tables at a quarter of their weight, +0.066
wins per game at the builder table and +0.064 at the table of searches, at 1.4
times the decision time. This is development-tier evidence: the protocol-arena
baseline stays `ntuple-leaf` until the blend wins a protocol cohort, and the
browser keeps the hand-written leaf.

## The previous protocol-arena baseline: expectimax-v2-plan

The corrected depth-3 candidate, frozen as `expectimax-v2-plan`, [won 47 of 80
authoritative games](../reports/expectimax-v2-plan-protocol.mdx) against 11 for
the compared ETA slot, with all 80 games valid; the registered rule (a 10-point
gap at p ≤ 0.05) is met at p = 1.0 × 10⁻⁶. New candidates should be compared
against this policy in a four-player table with the fixed builders. The
comparison is one lineup and one seat rotation scheme; strength against other
searches, humans, or negotiation-aware opponents is not established.


</AgentContext>
