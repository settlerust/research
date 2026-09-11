---
title: Autonomous research agents
summary: How an unattended agent takes one strategy direction from question to filed evidence in this repository without an orchestrator finishing its work.
navigation: false
---

# Autonomous research agents

An autonomous agent owns one direction end to end: it reads the approach brief,
frozen baseline, and prior findings; changes or adds policy code; registers a
falsifiable engine-arena comparison; runs it; files the record, a daily log
entry, a dated report, and the study metadata; and pushes a branch that the
canonical checkout can merge. Nothing is left for an orchestrator to write up.

## Where things are

| Repository | Path | What an agent touches |
| --- | --- | --- |
| research | `~/settlers/research` | Studies, registrations, records, logs, reports, analysis scripts |
| server | `~/settlers/server` | Rust engine, policies, the tunable search (`crates/expectimax/src/v2`), the engine arena (`crates/arena`) |
| design | `~/settlers/design` | React components and Storybook; new MDX components only |
| web | `~/settlers/web` | Renders the notebook; validators for report assets |

Read, in this order: `AGENTS.md`, `docs/research-workflow.md`,
`docs/experiment-program.md`, `docs/status.md`, the owning approach's
`README.mdx` and its `studies/*.toml`, `log/experiments.mdx`, and the last two
daily logs in `log/`. In the server read `docs/expectimax.md` (the search, its
leaf, the opening planner, bargaining, and the engine arena) before changing
search or policy code. Write prose with `.agents/skills/settlers-writing-style/SKILL.md`.

## Isolation

Every agent works on its own branches so that several can run at once.

```sh
cd ~/settlers/research && git fetch -q && git checkout -q dev && git pull -q --ff-only
just worktree NAME                       # research/.worktrees/NAME on branch research/NAME
cd ~/settlers/server && git fetch -q && git checkout -q dev && git pull -q --ff-only
git worktree add -b research/NAME ~/settlers/.worktrees/server-NAME dev
```

Point the research harness at the server worktree with
`SETTLERS_SERVER_DIR=~/settlers/.worktrees/server-NAME` for every `just`
command, and build the arena there:

```sh
cargo build --release -p settlers-arena --bin tournament --manifest-path ~/settlers/.worktrees/server-NAME/Cargo.toml
```

Use at most eight threads per tournament (`--threads 8`) because other agents
share the machine. Deterministic engine cohorts (`--deterministic`, node budgets
rather than time budgets) give the same games regardless of load; only wall
time changes.

## The evidence loop

1. State one falsifiable hypothesis about one mechanism. Hold everything else
   fixed: same search settings, same opponents, same seeds.
2. Screen cheaply: 16 seeds × 4 rotations without registration, to see whether
   the effect is large enough to be worth a cohort. Note screens in the daily
   log as screens, never as findings.
3. Register a development cohort with `just engine-register --study OWNER/SLUG
   --seats ... --seeds 0-63 --deterministic --hypothesis '...' --decision-rule '...'`
   and run it with `just engine-run EXPERIMENT`. The paired contrast is the
   candidate slot minus the control slot, with a 95% seed interval; 256 games
   resolve about ±0.1 wins per game, so effects smaller than that need more
   seeds or must be reported as inconclusive.
4. If the development cohort supports the hypothesis, register a confirmation on
   fresh seeds (for example 64-127) before recommending a default change.
5. File everything: the run record (generated), a dated `log/YYYY-MM-DD.mdx`
   entry with hypothesis, run IDs, interpretation, failures, and attribution
   (name the model that did the work), a report in `reports/SLUG.mdx` when the
   finding is worth reading, and the study TOML (`updated`, `status`, `outcome`,
   `next_step`, `reports`, `logs`). Then `just notebook`, `just check`, and, when
   web is present, `just site-check`.

A seating bias exists whenever two searches sit in slots 0 and 1: slot 1 is
always one seat after slot 0, and the arena asks recipients in turn order
after the offerer, so two identical default seats differ by +0.05 to +0.18
wins per game (reports/bargaining-arms.mdx). Never claim an effect from one
seating. Register every two-search contrast as a swapped pair on the same
boards (candidate in slot 0 with the control in slot 1, then the control in
slot 0 with the candidate in slot 1): the effect is half the difference of the
two contrasts and the seating term half their sum. A null pair (identical
seats in both slots) measures the bias directly when in doubt.

Report the two tiers honestly: engine-arena results are development evidence;
only the HTTP protocol arena confirms a frozen candidate. A screen is not a
finding. A cohort that loses or is inconclusive is still filed.

## Code changes

Keep the frozen reference (`expectimax-v1`) untouched. Put a new mechanism
behind a `SearchConfig` switch or weight with a default that reproduces the
current behaviour unless the evidence loop above justifies a new default.
Every arena seat spec is JSON, so a candidate is `v2:{"depth":2,"your_switch":true}`
and its control is `v2:{"depth":2}`. Add a focused test under
`crates/expectimax/tests/` for the mechanism, run `cargo fmt --all`, `cargo
clippy --workspace --all-targets --all-features --locked -- -D warnings`, and
`cargo test -p settlers-expectimax`, and document the switch in
`docs/expectimax.md`.

New visual components belong in the design repository's Storybook with a typed
asset schema and a matching web validator; an MDX report may only embed
registered design components.

## Finishing

Commit on the agent's branches with clear messages. Then integrate: rebase the
research branch on `origin/dev`, merge it into the canonical `dev` checkout,
run `just notebook` and `just check` there, and push. Do the same for the
server branch when its checks pass. If a merge conflicts in a generated file,
regenerate it with `just notebook` rather than editing it by hand; if a conflict
cannot be resolved, push the branch and describe the conflict at the end of the
daily log entry so a reviewer can finish the merge. End with a short summary of
the hypothesis, the contrast with its interval, and the recommended next step.
