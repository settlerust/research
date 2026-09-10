# Current evidence boundary

This repository starts with a headless protocol harness, existing Rust fast/ETA
opponents, and a minimal Python policy adapter. Setup and smoke validation do
not establish a strategy ranking. No claim of optimal play has been made.

Consult `records/runs/` for actual run outcomes and `reports/` for selected
publications. Promote a finding here only when a fixed candidate, retained
artifacts, complete denominators, and the stated decision rule support it.

The [strategy atlas](../approaches/README.md) now defines sixteen proposed directions, with animated mechanisms, study briefs, and a shared [experiment program](experiment-program.md). No new strategy evaluation was run to create this guide. Interactive teaching values and synthetic publishing fixtures remain explicitly separate from recorded evidence.


## First strategy comparison: retain ETA

The [liquidity experiment](../reports/liquidity-baseline.mdx) completed all 80
registered evaluation games in run `de39917c-55da-40ad-a53a-5b8588898810`.
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

## The previous protocol-arena baseline: expectimax-v2-plan

The corrected depth-3 candidate, frozen as `expectimax-v2-plan`, [won 47 of 80
authoritative games](../reports/expectimax-v2-plan-protocol.mdx) against 11 for
the compared ETA slot, with all 80 games valid; the registered rule (a 10-point
gap at p ≤ 0.05) is met at p = 1.0 × 10⁻⁶. New candidates should be compared
against this policy in a four-player table with the fixed builders. The
comparison is one lineup and one seat rotation scheme; strength against other
searches, humans, or negotiation-aware opponents is not established.

