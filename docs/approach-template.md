---
title: Approach authoring template
summary: Keep new ideas visual, falsifiable, and honest about their evidence.
---

# Approach authoring template

Use this structure for a new `approaches/<id>/README.mdx`. Add its own explanatory SVG to the design Storybook and register it before embedding it. Add a catalogue item linking the page. Reuse chart primitives; do not reuse a generic illustration when the mechanism differs.

```mdx
---
title: A concrete strategy name
summary: The decision this approach helps a player make.
status: proposal
evidence: none
---

# A concrete strategy name

One sentence naming the decision at the table.

<StrategyFigure approach="registered-id" />

## The decision at the table

A concrete Catan situation and why it is difficult.

## The mechanism to test

The inputs, computation, and decision. Name uncertainty and information boundaries.

## Proposed experiment

A falsifiable hypothesis, isolated treatment, fixed comparison, and primary outcome.
Describe the chart or replay that would expose the mechanism.

## What could disprove it

Failure modes, confounds, and the result that would change your mind.

<AgentContext>
Implementation prerequisites; executable versions; registration and run IDs when
available; source references; full metrics; limitations; reproduction commands.
</AgentContext>
```

After a completed study, add a concise finding and a sourced exhibit. Retain the original hypothesis and link the frozen registration and run records. Do not rewrite a failed test as if it had proposed the successful idea all along.

Create bounded investigations with `just study APPROACH/SLUG --title ... --question ...`.
They live in this approach's `studies/` directory; `just notebook` maintains the
linked investigation section in the approach page. Keep the hand-written mechanism
and evidence boundary current as well. See [the research workflow](research-workflow.md).
