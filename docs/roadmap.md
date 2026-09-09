---
title: Roadmap
summary: The open questions across resource planning, uncertainty, conversation, social strategy, and generalization, with evidence and prerequisites for each stage.
---

# Roadmap

How do we build a player that handles both the island and the people around it? These are the open research questions, ordered by their dependencies. They are proposed investigations, not scheduled runs or demonstrated improvements. Every linked approach has a mechanism figure and a falsifiable study design.

## Where the evidence stands

The arena completes real ten-point games and retains public observations and event tapes. The first frozen [liquidity comparison](../reports/liquidity-baseline.mdx) completed 80/80 games: liquidity won 20 and ETA control won 26. The improvement rule failed, so ETA remains the baseline. That finding concerns one estimator at one fixed table.

An offline [engine arena](../reports/engine-arena-calibration.mdx) now plays paired-seed games in seconds and reproduces the protocol ordering. The [corrected tunable search](../reports/expectimax-v2-corrected.mdx) wins 50.4% of paired slot-games at depth 2 and 57.4% at depth 3 against ETA builders, and its frozen depth-3 candidate [won 47 of 80 authoritative games](../reports/expectimax-v2-plan-protocol.mdx) to become the protocol baseline; the [tree-structure report](../reports/tree-structure.mdx) measures how wide a turn is and what each planned turn costs. The broader questions below remain open.

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
| 2026-09-09 | [Engine arena: paired-seed offline tournaments](/research/reports/engine-arena-calibration) | Active | The engine arena reproduces the protocol ordering (ETA beats fast on 128 paired boards; the frozen reference loses to both). Deterministic mode now gives both tiers seed-indexed dice, theft, and deck tapes; a protocol smoke confirmed identical rolls across rotations. Next: Use the arena for development sweeps and structure measurements; confirm any frozen candidate with a fresh protocol cohort. [Log 2026-09-08](/research/log/2026-09-08) · [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Game tree structure](/research/reports/tree-structure) | Active | Median legal actions: 8 in the main phase, 22 for the robber, 1 for rolls and discards; the main phase widens from 2 to 9 through a game. Each planned turn multiplies expectimax-v2 work by four to six; depth 3 costs about 0.5 s natively and WASM is 1.3 times slower. Next: Measure how much of the raw legal list the candidate generator prunes, and the cost of the confirmed depth-3 candidate under contention. [Log 2026-09-08](/research/log/2026-09-08) · [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Exchange-aware ETA](/research/reports/liquidity-baseline) | Active | The frozen 80-game comparison did not meet its improvement rule. Retain ETA as the baseline. Next: Record decision traces before proposing a new estimator; port acquisition remains an open question. [Liquidity statistics](/research/reports/liquidity-statistics) · [Liquidity audit](/research/reports/liquidity-audit) · [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [A tunable turn-level expectimax](/research/reports/expectimax-v2-development) | Active | The corrected depth-3 candidate (expectimax-v2-plan) won 47 of 80 authoritative games against 11 for the compared ETA slot (p = 1.0e-6), meeting its rule; engine arena: depth 2 wins 50.4% and depth 3 57.4% of paired slot-games against ETA, and 46.9% against the frozen reference. Next: Tune the leaf weights and inclinations on unregistered sweeps against the new baseline, measure WASM cost per depth in the browser, and test a response-aware opponent model. [Expectimax v2 protocol](/research/reports/expectimax-v2-protocol) · [Expectimax v2 corrected](/research/reports/expectimax-v2-corrected) · [Expectimax v2 plan protocol](/research/reports/expectimax-v2-plan-protocol) · [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Leaf-guided opponents versus the builder model](/research/approaches/adaptation) | Active | Round one, 256 deterministic games: contrast -0.008 wins per game (95% interval -0.111 to +0.096). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Proposing trades versus never proposing](/research/approaches/bargaining) | Active | Round one, 256 deterministic games: contrast -0.027 wins per game (95% interval -0.132 to +0.077). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Maximal trade openness](/research/approaches/bargaining) | Active | Round one, 256 deterministic games: contrast -0.094 wins per game (95% interval -0.192 to +0.005). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Hidden hands sampled from event history versus public counts only](/research/approaches/beliefs) | Active | Round one, 256 deterministic games: contrast -0.090 wins per game (95% interval -0.201 to +0.021). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [One sampled world versus four](/research/approaches/beliefs) | Active | Round one, 256 deterministic games: contrast -0.051 wins per game (95% interval -0.166 to +0.064). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Maximal aggression](/research/approaches/containment) | Active | Round one, 256 deterministic games: contrast +0.020 wins per game (95% interval -0.084 to +0.123). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Opponent progress and production terms](/research/approaches/containment) | Active | Round one, 256 deterministic games: contrast +0.000 wins per game (95% interval -0.105 to +0.105). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [A maximal development-card appetite](/research/approaches/development) | Active | Round one, 256 deterministic games: contrast +0.031 wins per game (95% interval -0.070 to +0.132). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Development card and knight terms](/research/approaches/development) | Active | Round one, 256 deterministic games: contrast -0.035 wins per game (95% interval -0.144 to +0.074). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Reachable-site value and road contention terms](/research/approaches/expansion) | Active | Round one, 256 deterministic games: contrast -0.074 wins per game (95% interval -0.169 to +0.021). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Ablations: what each mechanism is worth](/research/reports/ablations) | Active | Round one of eighteen one-change arms: removing lookahead costs -0.324 wins per game and two scenarios instead of eight costs -0.410; every leaf term and slider is within 0.1 with an interval crossing zero. Next: Complete the six fresh-seed confirmations and the reciprocity arm, then retest the surviving mechanisms under the depth-3 candidate. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Placing the opening with the search instead of the builder heuristic](/research/approaches/opening) | Active | Round one, 256 deterministic games: contrast -0.035 wins per game (95% interval -0.133 to +0.062). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Cross-play of four search styles](/research/approaches/population) | Active | Four inclination presets split 256 deterministic games almost evenly (66, 59, 69, 62 wins); no preset dominates. Next: Cross-play at depth 3 and against the frozen reference, then a heatmap of pairwise contrasts. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Port value terms](/research/approaches/ports) | Active | Round one, 256 deterministic games: contrast +0.020 wins per game (95% interval -0.086 to +0.125). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Learning who accepts](/research/approaches/reputation) | Active | Round one, 256 deterministic games: contrast -0.031 (interval -0.125 to +0.063); no effect against fixed builders. Next: Test reciprocity against an opponent whose acceptance depends on history, for example a second search seat with the same model. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [The discard-exposure term](/research/approaches/risk) | Active | Round one, 256 deterministic games: contrast -0.023 wins per game (95% interval -0.134 to +0.087). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [A maximally risk-seeking style](/research/approaches/risk) | Active | Round one, 256 deterministic games: contrast -0.062 wins per game (95% interval -0.175 to +0.050). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Static turn planning versus one round of lookahead](/research/approaches/search) | Active | Round one, 256 deterministic games: contrast -0.324 wins per game (95% interval -0.413 to -0.235). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [Two common random scenarios versus eight](/research/approaches/search) | Active | Round one, 256 deterministic games: contrast -0.410 wins per game (95% interval -0.489 to -0.331). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |
| 2026-09-09 | [The acquisition-time plan term](/research/approaches/tempo) | Active | Round one, 256 deterministic games: contrast +0.062 wins per game (95% interval -0.039 to +0.164). See the ablation report. Next: Read the confirmation cohort on fresh seeds where registered; otherwise retest under the confirmed depth-3 candidate before changing defaults. [Log 2026-09-09](/research/log/2026-09-09) |

[research-studies:end]: #
