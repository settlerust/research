# Liquidity: an exchange-aware ETA builder

A research-owned Rust policy crate. `eta-control` and `fast-control` preserve the
local server's heuristic planners; `liquidity` changes only the analytical target
ETA. All three use the same runner and trading wrapper. This is an executable
heuristic experiment, not expectimax and not a claim of optimal play.

Build from the research repository with `just build-liquidity`; Rust dependencies
come from a sibling `server` checkout. `just smoke-liquidity` builds successfully
before registering and running four protocol games. Use `SETTLERS_SERVER_URL`
to select the endpoint. The standard registry exposes all three policies.

## The one strategic change

The control estimates waiting time as the largest resource deficit divided by
that resource's production rate plus the existing 0.025 smoothing constant.
The candidate projects the hand at a proposed time, reserves the target's cards,
and counts **whole** surplus exchange bundles at its current 4:1, 3:1, or 2:1
rates. A 32-step binary search finds the earliest feasible projected time, bounded
above by the original estimate. Production rates, smoothing, gain weights, road
penalties, expansion search and tie breaking remain shared.

This is a deterministic mean-income proxy, not a stochastic expected hitting
time. It ignores robber blocking, waiting-time variance, discards and future
bank shortages. Legal execution still comes from the server. It values existing
ports; it does not explicitly plan to acquire one.

The changed target also changes which resources the bot preserves, requests,
and seeks through legal bank trades. Trade acceptance deliberately keeps the
original fast-planner target, as in the existing ETA baseline. This experiment
does not redesign bargaining, promises, reputation, or truthfulness.

## Shared protocol adaptations

The current protocol requires connected players to send `SetReady`. The shared
runner does that, reuses its own seat token, and retries the **same** command
envelope on transport ambiguity or storage backpressure. Other non-race server
errors terminate the process. Each policy decision is checked against five
seconds; the harness additionally enforces the match wall-clock cap.

Every policy receives 16 trade-offer attempts per game, conservatively respecting
the server's 16-message/minute limit at headless speed. Acceptance is uncapped.
Failed offer attempts also consume this local budget. This is a study condition,
not an assertion that the budget is strategically best.

`provenance.toml` records the original server files' hashes. The run manifest
freezes authored Rust sources, Cargo.lock, and the actual configured executable
hash. Game randomness is server-generated and unavailable to these processes.
