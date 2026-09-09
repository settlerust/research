---
title: Roadmap
summary: The open questions across resource planning, uncertainty, conversation, social strategy, and generalization, with evidence and prerequisites for each stage.
---

# Roadmap

How do we build a player that handles both the island and the people around it? These are the open research questions, ordered by their dependencies. They are proposed investigations, not scheduled runs or demonstrated improvements. Every linked approach has a mechanism figure and a falsifiable study design.

## Where the evidence stands

The arena completes real ten-point games and retains public observations and event tapes. The first frozen [liquidity comparison](../reports/liquidity-baseline.mdx) completed 80/80 games: liquidity won 20 and ETA control won 26. The improvement rule failed, so ETA remains the baseline. That finding concerns one estimator at one fixed table; the broader questions below remain open.

## 1. Make resources turn into points

The next mechanical studies should explain why a plan succeeds or stalls while holding placement, trading rules, and opponents fixed.

| Open question | Investigation | What would move us forward? |
| --- | --- | --- |
| Which opening resource mix supports a coherent build plan? | [Opening portfolios](../approaches/opening/README.mdx) | A frozen placement contrast with build-time and bottleneck diagnostics |
| Does identifying the next scarce resource improve build timing? | [Build tempo](../approaches/tempo/README.mdx) | Faster useful builds and a fresh game-level evaluation; revisit the liquidity result before adding complexity |
| When is a road worth building before an opponent closes the route? | [Expansion and races](../approaches/expansion/README.mdx) | Recorded contested-site decisions and opportunity costs |
| When does port access beat bargaining or broader production? | [Ports and market power](../approaches/ports/README.mdx) | A contrast that includes the cost of reaching the coast |

## 2. Plan with uncertainty

Before granting more search or a stronger model, fix a common decision deadline and reference policy. Better predictions should be calibrated on held-out events and should improve decisions at equal cost.

| Open question | Investigation | What would move us forward? |
| --- | --- | --- |
| Can public production and spending support useful hidden-hand beliefs? | [Beliefs](../approaches/beliefs/README.mdx) | Calibrated predictions with no hidden-state leakage |
| Which branches deserve a limited search budget? | [Search](../approaches/search/README.mdx) | A quality-versus-latency frontier against a fixed reference |
| Should a leader and a trailing player choose different risks? | [Risk and timing](../approaches/risk/README.mdx) | Outcome distributions and predeclared position-dependent contrasts |
| When should development cards become tempo, awards, or surprise points? | [Development](../approaches/development/README.mdx) | Public card-use timelines and fresh complete-game outcomes |

## 3. Find out what conversation changes

First establish that an opponent can receive and respond to messages. Then compare the same offers with silence, a request, and a truthful explanation, under equal message budgets and response windows. Changing the offer and the wording together would leave the cause unclear.

| Open question | Investigation | What would move us forward? |
| --- | --- | --- |
| How should an offer price both players' next builds? | [Bilateral bargaining](../approaches/bargaining/README.mdx) | Bilateral value estimates plus actual responses |
| Can a checkable reason help a useful offer get accepted? | [Truthful signals](../approaches/signals/README.mdx) | Identical-offer message contrasts and an offer-response timeline |
| How do disclosure, false claims, and broken promises change later behavior? | [Bluffs and disclosure](../approaches/deception/README.mdx) | Separate treatments with belief and credibility diagnostics |

## 4. Test whether social decisions pay back

These studies depend on reliable event memory, a frozen reference valuation, and identifiable recipients. Keep the immediate cost of a concession visible; an eligibility threshold for a model call does not enforce a concession cap.

| Open question | Investigation | What would move us forward? |
| --- | --- | --- |
| Does another player repay a costly concession? | [Reciprocity and reputation](../approaches/reputation/README.mdx) | Recipient-specific continuation evidence, including unrepaid costs |
| Can social context improve choices inside a strict foregone-value budget? | [Bounded pliability](../approaches/pliability/README.mdx) | Verified cap enforcement and win-versus-cost analysis |
| Who should pay to slow a leader? | [Leader containment](../approaches/containment/README.mdx) | Threat estimates, blocking costs, and each player's own route to victory |

## 5. Check whether gains survive unfamiliar tables

A policy that wins against one lineup may exploit a narrow weakness. Freeze candidates before testing fresh opponents and keep the full four-player lineup in the analysis.

| Open question | Investigation | What would move us forward? |
| --- | --- | --- |
| Can a player adapt without overreacting to one refusal? | [Opponent adaptation](../approaches/adaptation/README.mdx) | Held-out predictions and controlled response changes |
| Does training a diverse population produce broadly useful policies? | [Population and self-play](../approaches/population/README.mdx) | Cross-play tables with complete denominators, uncertainty, and visible matchup cycles |

## Choose the next experiment

Start with the smallest contrast that resolves an uncertainty. Useful next candidates are a bottleneck diagnostic for the existing estimator result, or a message-only study after verifying responsive opponents. No candidate is promoted by a plausible animation or a few successful games.

Use the [Research experiment program](experiment-program.md) to register the hypothesis, budget, opponents, stop rule, and decision rule. Preserve failed and incomplete attempts. A negative result that rules out a mechanism is a useful completed contribution; update the [evidence boundary](status.md) when new retained evidence supports it.

[research-studies:start]: #

## Tracked investigations

| Updated | Investigation | Status | Finding and next step |
| --- | --- | --- | --- |
| 2026-09-08 | [Protocol and replay validation](/research/reports/baseline-smoke) | Active | The harness completes normal games with Rust and Python policies. Smoke results establish plumbing, not policy strength. Next: Repeat a bounded smoke after protocol changes and retain every failed or interrupted attempt. [Log 2026-09-08](/research/log/2026-09-08) |
| 2026-09-08 | [Engine arena: paired-seed offline tournaments](/research/reports/engine-arena-calibration) | Active | The engine arena reproduces the protocol arena ordering: ETA beats fast on 128 paired boards, and the frozen reference loses to both builders. Next: Use the arena for development sweeps and structure measurements; confirm any frozen candidate with a fresh protocol cohort. [Log 2026-09-08](/research/log/2026-09-08) |
| 2026-09-08 | [Game tree structure](/research/docs/experiment-program) | Active | No experiment has been executed. Next: Register a fixed candidate, comparison, budget, and decision rule. [Log 2026-09-08](/research/log/2026-09-08) |
| 2026-09-08 | [Exchange-aware ETA](/research/reports/liquidity-baseline) | Complete | The frozen 80-game comparison did not meet its improvement rule. Retain ETA as the baseline. Next: Record decision traces before proposing a new estimator; port acquisition remains an open question. [Liquidity statistics](/research/reports/liquidity-statistics) · [Liquidity audit](/research/reports/liquidity-audit) · [Log 2026-09-08](/research/log/2026-09-08) |
| 2026-09-09 | [A tunable turn-level expectimax](/research/reports/expectimax-v2-development) | Active | Engine arena: depth 2 wins 34.0% of 256 paired slot-games against ETA (contrast +0.098, interval +0.005 to +0.190). Protocol arena: the frozen depth-3 candidate won 38.8% of 80 games against the compared ETA slot's 31.2%, short of the registered 10-point rule (p = 0.25). Positive direction, not confirmed. Next: Fix the turn-planning bug found after these cohorts, retune the leaf, and register fresh engine and protocol cohorts for the corrected candidate. [Expectimax v2 protocol](/research/reports/expectimax-v2-protocol) · [Log 2026-09-08](/research/log/2026-09-08) · [Log 2026-09-09](/research/log/2026-09-09) |

[research-studies:end]: #
