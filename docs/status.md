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
paired slot-games against ETA's 20.3% (paired contrast +0.301, interval +0.190
to +0.412), still engine-arena evidence. A corrected candidate is registered for
a fresh protocol cohort; until it completes, the protocol baseline remains ETA.

