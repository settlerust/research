---
title: Research concepts
summary: Short explanations of win rates, uncertainty, paired games, and the two experiment arenas.
---

# Research concepts

## Win rate

Wins divided by completed games for one competitor slot. A result of 46 wins in 80 completed games is 57.5%. Report incomplete and unplayed games separately; neither is a loss.

## Paired contrast

The difference in wins per game between the candidate and its control. A contrast of +0.066 means 6.6 more wins per 100 games on average in that comparison. It is a difference between rates, not a relative percentage improvement.

## Confidence interval

An interval describes the uncertainty around an estimate under the analysis's assumptions. If a contrast's 95% interval includes zero, the data leave its direction unresolved. An interval excluding zero still needs to meet the registered decision rule; it does not establish strength against every opponent.

## Swapped pairs

Run both candidate/control seat orders on the same boards, then average the paired contrasts. This separates a policy change from a turn-order advantage. Repeating only one seating can make identical policies look different.

## Engine arena

An offline runner using the same Rust game engine, with explicit boards and only redacted observations reaching each policy. It supports quick development and diagnosis. It does not exercise the server transport, timing, or complete deployment path.

## Protocol arena

Clients play through the authoritative local game server. This checks the policy's actual observation, command, event, and timeout behavior. A fixed protocol cohort is needed before changing the confirmed server baseline.

## Learned leaf

The value estimate at the end of a search. The learned leaf looks up trained pattern values; the hand-written leaf uses explicit heuristics. Comparing them inside the same search isolates the value estimate from the search itself.

## Smoke run

A small run that checks whether the system starts, plays, finishes, and records its evidence. Its purpose is operational validation. A handful of games cannot establish strategic superiority.
