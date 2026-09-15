---
date: "2026-09-08"
title: Liquidity statistics and reproduction
summary: The primary contrast, uncertainty, source hashes and reproducible analysis.
---

# Liquidity statistics and reproduction

The frozen evaluation ran on 2026-09-08 in America/Los_Angeles (2026-09-09 UTC).
The process used a dedicated local server on port 5566, with its own local data.
The server and policies were release Rust binaries on macOS. All 80 games completed
validly; no timeouts, incomplete games or unplayed matches entered the denominator.

| Slot / policy | Wins | Losses | Completed | Win rate | 95% Wilson interval | Mean points |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| 0 / liquidity | 20 | 60 | 80 | 25.0% | 16.8%–35.5% | 7.44 |
| 1 / eta-control | 26 | 54 | 80 | 32.5% | 23.2%–43.4% | 7.75 |
| 2 / fast-control | 13 | 67 | 80 | 16.2% | 9.7%–25.8% | 7.29 |
| 3 / fast-control | 21 | 59 | 80 | 26.2% | 17.9%–36.8% | 7.50 |

## Primary contrast

Each game contributes +1 when Liquidity wins, −1 when ETA wins, or 0 when either
Fast slot wins. The average is −0.075. This preserves the game as the unit of
analysis; the two Fast slots are not pooled into 160 independent observations.

Among the 46 games won by either primary slot, Liquidity won 20. The exact
one-sided binomial tail under equal win probabilities is 0.8490021934. Promotion
required p ≤ 0.05 and an observed gain of at least 0.10. Neither condition passed.

An exploratory, non-preregistered percentile bootstrap resampled whole games
20,000 times, giving [−0.2375, 0.0875] for the win-rate difference. Resampling seed
20260908 belongs only to analysis; it never entered a game. The source code retains
the exact percentile indexing. This interval does not establish equivalence or
prove the candidate is inferior.

## Descriptive mechanism checks

| Metric per completed game | Liquidity | ETA control |
| --- | ---: | ---: |
| Bank/port exchanges | 6.3375 | 5.8625 |
| Discarded cards | 10.1625 | 8.7125 |
| Cities built | 2.6500 | 2.4875 |
| Roads built, including setup | 6.2125 | 6.6375 |

Mean final-point difference: −0.3125. Exact score comparisons: 35 ahead, 39 behind,
6 tied. The heatmap bins final scores as 2–4, 5–6, 7–8, 9 and 10+. Its cells sum to
80 games. The exchange plot is an empirical CDF at integer trade-count thresholds;
line segments connect observed thresholds rather than estimating a continuous law.
These are descriptive secondary measures, without multiple significance tests.

## Reproduce the analysis

From the research checkout, with the verified raw run locally available:

<AgentContext title="Run the archived analysis">

```sh
python3 -m analysis.liquidity de39917c-55da-40ad-a53a-5b8588898810
just check
```

</AgentContext>

The script validates the finalized inventory before reading result rows and public
rule events. It writes ignored per-game rows and analysis output under
`.runtime/analysis/`, plus the two curated diagnostic plots. It refuses partial
cohorts. It never reads player observations, credentials or private process logs.
The win chart and replay originate from `just publish`; their presentation labels
were edited without changing the recorded values.

To build this policy for a **new** registered experiment:

```sh
just build-liquidity
```

Use the `liquidity`, `eta-control` and `fast-control` registry entries. A rerun has
fresh server randomness and must not be described as a reproduction of the same
random stream. No seed is exposed. Seat rotation gives each slot 20 games in each
seat, without pairing seeds or fixing the starting player.

## Evidence identity

- Experiment: [registered protocol](https://github.com/settlerust/research/blob/dev/experiments/d9cbd52e-0a90-4c4b-8fae-23c0372f1d6e.toml).
- [Run record](../records/runs/de39917c-55da-40ad-a53a-5b8588898810.md).
- Inventory SHA-256: `063a024a2f341520bdf1188904b7ddc66a23836087fb7a14abef06c976ab6046`.
- Analysis source SHA-256: `f22fc5d15a3c27cd6e0de0e4c17ff51506159974bbfca5775061f25a95d47898`.
- Shared policy executable SHA-256: `0aaf22a660fa70fbb2944a5a61e5560cd3d14b0b427000d31641effbf124d9a3`.
- Server executable SHA-256: `5b6ade55b0a6bde720f4238d807eaa0c9f3b93c4d65e2cf969bb7c3588ede29f`.

The manifest retains the experiment, source snapshots, Cargo.lock, configured
executable hashes and Git states. The executable is identical to the final
successful smoke; the frozen policy sources were checked unchanged after the run.
The policies were built from dirty working trees, not a named release.

The verified bundle is [80-game protocol cohort](/research/records/runs/de39917c-55da-40ad-a53a-5b8588898810).
See its [archive receipt](https://github.com/settlerust/research/blob/dev/records/artifacts/de39917c-55da-40ad-a53a-5b8588898810.md).
Archive SHA-256: `6535a03b78dcb8bac31e0100ce872a8c27b4ee59ae6902397e0bbb103eb99a54`.
Local integrity does not imply a remote backup.

[Main report](liquidity-baseline.mdx) · [All excluded runs](liquidity-audit.md).
