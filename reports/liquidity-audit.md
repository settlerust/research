---
date: "2026-09-08"
title: Liquidity study audit trail
summary: Every startup failure, protocol repair, smoke cohort and excluded evaluation.
---

# Liquidity study audit trail

The primary result uses only the fresh 80-game cohort. Earlier outcomes were never
pooled into its denominator. The strategic estimator stayed unchanged throughout
protocol repairs. Completed experiment files and run inventories were retained.

| Run | Planned | Attempted | Complete | Incomplete | Unplayed | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [d63fca03](../records/runs/d63fca03-97af-461a-8956-c2926fe6f57a.md) | 4 | 1 | 0 | 1 | 3 | Startup timeout; legacy runner omitted SetReady. |
| [74e9d98a](../records/runs/74e9d98a-966c-4bc7-92b6-471b97168394.md) | 4 | 1 | 0 | 1 | 3 | Confirmed sockets connect; the unchanged legacy startup still failed. |
| [0bd1bc93](../records/runs/0bd1bc93-49c5-49b0-bfc0-d476a8466d39.md) | 4 | 1 | 0 | 1 | 3 | Added native startup diagnostics; connected sockets still did not become ready. |
| [7459585e](../records/runs/7459585e-6a49-4484-aa59-a9cdc70013b1.md) | 4 | 1 | 0 | 1 | 3 | Harness diagnostics identified readiness rejection being misreported as a connection timeout. |
| [1201e0ae](../records/runs/1201e0ae-a1dc-4606-934c-f96ed0fb286a.md) | 4 | 2 | 1 | 1 | 2 | Readiness repaired. The second game hit the server communication cap; stopped. |
| [fda25b9d](../records/runs/fda25b9d-56e0-487e-8b3b-ed328080f531.md) | 4 | 4 | 4 | 0 | 0 | Four-game smoke after the shared 16-offer budget; no strength inference. |
| [83f0efb5](../records/runs/83f0efb5-0d42-47d8-a53c-99f136d55a80.md) | 80 | 3 | 2 | 1 | 77 | First evaluation stopped at archive backpressure; 77 games deliberately left unplayed. |
| [5a18c7f0](../records/runs/5a18c7f0-df67-488a-bd61-ec2bd164ff68.md) | 4 | 4 | 4 | 0 | 0 | Excluded smoke: a build syntax error let an unguarded command sequence use the previous executable. Actual binary hash retained; not validation of the retry fix. |
| [4486b5cc](../records/runs/4486b5cc-a660-42a4-b492-8f48dbe9be00.md) | 4 | 4 | 4 | 0 | 0 | Guarded build and four-game smoke of the final retry-capable runner. |

## Changes made before the fresh evaluation

- The shared native runner marks its own connected seat ready.
- All policies get the same 16 offer attempts per game, including attempts lost to a race. Trade acceptance remains available.
- Storage backpressure and transport ambiguity retry the identical command envelope with bounded backoff. Rule errors still stop the run.
- The harness reports startup readiness accurately, hashes research-owned executables and Cargo.lock, excludes generated target trees, and strips research-spectator theft details and directed chat from new public tapes.
- `just smoke-liquidity` depends on a successful format check, tests, Clippy and release build, preventing a failed rebuild from silently launching an old binary.

These adaptations define the tested baseline. No estimator weights were tuned
against the failed evaluation or smoke outcomes.

## What is retained

Each linked run record names its experiment, manifest digest and inventory digest.
Verified local bundles live in `artifacts/liquidity-study/`; their immutable
receipts are in `records/artifacts/`. The earlier diagnostic tapes predate the
public-event filter and can include research-spectator theft details. They remain
local diagnostic evidence and are not used for the public charts or replay.
Credentials, participant observations and private process logs are not included
in the bundles. There is no remote backup or public download URL.

Small connection diagnostics reused already failed lobbies without starting games.
They produced no additional match outcomes. A runtime syntax failure is recorded
above instead of being hidden as an unreported tuning attempt.

[Return to the experiment](liquidity-baseline.mdx).
