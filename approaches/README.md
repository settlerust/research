---
title: Strategy atlas
summary: Seventeen visual study briefs covering the island, uncertainty, learning, conversation, and the whole table.
---

# Strategy atlas

A well-rounded player needs several kinds of judgment. Explore an idea, inspect its mechanism, and follow it to the experiment that could support or disprove it.

<StrategyAtlas asset="strategy-atlas" />

Start with the [player’s guide](../docs/strategy-guide.mdx) for the big picture, or the [pliability laboratory](pliability/README.mdx) for the tradeoff between a search recommendation and future cooperation. The [experiment program](../docs/experiment-program.md) turns these directions into controlled comparisons.

The registered `fast` and `eta` opponents come from the server’s Rust policy crate. `legal-first` is a legality and protocol example. `expectimax-v1` is the frozen reference search and `expectimax-v2` the tunable search studied under [search](search/README.mdx). The other study briefs are proposals; they do not imply implemented policies.

Each approach keeps its bounded investigations in `studies/`. Their dated findings
appear below the approach explanation and in the [experiment log](../log/experiments.mdx).
See [the research workflow](../docs/research-workflow.md) when adding or continuing a study.
