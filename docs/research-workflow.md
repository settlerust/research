---
title: Keeping the research notebook current
summary: Where investigations belong and how their evidence becomes an updated approach, experiment log, and site page.
navigation: false
---

# Keeping the research notebook current

Every investigation has one home and a visible next step. A study groups a
question, its registrations, findings, and failed attempts. An experiment is one
frozen protocol; a run is one execution of it. Grouping them never merges their
statistical denominators.

## Choose a home

| Material | Location | Purpose |
| --- | --- | --- |
| Approach explanation | `approaches/APPROACH/README.mdx` | Mechanism, proposal, evidence boundary, and linked investigations |
| Approach study | `approaches/APPROACH/studies/SLUG.toml` | Ownership, dates, status, conclusion, next step, and document references |
| Cross-cutting study | `log/studies/SLUG.toml` | Protocol, infrastructure, or comparison work without a single approach |
| Frozen registration | `experiments/UUID.toml` | Exact hypothesis, full lineup, budgets, and decision rule; carries a study ID |
| Policy and analysis source | `policies/` and `analysis/` | Reproducible implementation shared by its linked studies |
| Daily interpretation | `log/YYYY-MM-DD.mdx` | What changed, why, failures, run IDs, and actual attribution |
| Public report and exhibits | `reports/SLUG.mdx`, `content/assets/` | Dated findings and bounded, validated figures/replays |
| Durable evidence trail | `records/runs/`, `records/artifacts/` | Compact internal outcome records and verified archive receipts |
| Local evidence and runtime | `runs/`, `artifacts/`, `.runtime/` | Ignored raw data, archives, server state, and private logs |
| Temporary isolated checkout | `.worktrees/NAME/` | Ignored branch workspace inside the canonical research directory |

The [experiment log](../log/experiments.mdx) is generated from study metadata.
It links readable reports and dated notes. Raw run records remain reproduction
details, outside the notebook navigation and search.

## Start a bounded investigation

Look for an existing study first. Use an approach owner when the question belongs
to one of the strategy briefs; use `log/SLUG` for cross-cutting work. A related
approach can link to the owning study's report without creating a second copy.

```sh
just study tempo/bottleneck-trace \
  --title 'Trace the next build bottleneck' \
  --question 'Does the estimator choose the wrong scarce resource before a stalled build?'
just register --study tempo/bottleneck-trace \
  --players liquidity eta-control fast-control fast-control --games 80 \
  --hypothesis 'State the isolated treatment and falsifiable prediction.' \
  --decision-rule 'State the fixed primary contrast and promotion threshold.'
```

The commands illustrate filing, not a ready-to-run scientific design. Freeze the
actual candidate, counts, and decision rule using the [experiment program](experiment-program.md).
Set the study to `active` when work starts. `proposed`, `active`, `blocked`, and
`complete` describe progress; `complete` does not mean the hypothesis succeeded.
A completed study stays complete: create a follow-up for a new question or cohort.

Candidate smoke matches also take `--study tempo/bottleneck-trace`. The default
for plain `just match` is the ongoing `log/protocol-smoke` investigation. Existing
registrations retain their exact bytes; study `legacy_experiments` arrays file
historical UUIDs without changing the preregistration or its recorded digest.

## Close the documentation loop

1. Retain the run record, including invalid, censored, and interrupted attempts.
   Archive finalized evidence and preserve its verified receipt.
2. Append the daily log with the hypothesis, interpretation, limitations, failures,
   run IDs, and actual contributor/model or `unknown`. Long attempt histories can
   live in an explicitly linked audit. Add the daily path to the study's `logs`.
3. Write a dated report for findings worth reading. Use the [publishing guide](publishing.md)
   for figures and public replays. Add every report to exactly one study's `reports`,
   with its main report first and supporting analyses/audits afterward.
4. Update the study's `updated`, `status`, `outcome`, `next_step`, and `attribution`.
   Revise the approach prose and [evidence boundary](status.md) when warranted.
5. Run `just notebook`, then `just check` and `just site-check`. Integrate these
   source and documentation changes together before declaring the investigation done.

`just notebook` refreshes `log/experiments.mdx` and the marked investigation
sections in the owning approaches and roadmap. Edit the TOML source, not these
generated sections. It does not invent a conclusion or overwrite hand-written
proposals. Checks reject unfiled experiments and reports, missing references,
undocumented run records, invalid dates, and stale generated sections. Research
CI and the website's prebuild both enforce the same check.

## Isolated work stays inside research

From a clean, integrated source checkout, use `just worktree NAME`. It creates
branch `research/NAME` beneath the canonical `research/.worktrees/`, even when
invoked from another linked worktree. It refuses a dirty source because Git would
leave uncommitted changes behind. A branch in the canonical checkout is also an
option when no concurrent research is underway; preserve existing work.
`just check` also rejects registered worktrees outside the canonical `.worktrees/`.

The harness resolves its default server against the canonical checkout, so nested
worktrees still use `settlers/server`. `SETTLERS_SERVER_DIR` and
`SETTLERS_SERVER_URL` remain explicit overrides. Running a separate local server
requires a separate port and its worktree-owned runtime storage.

Integrate policy code, analyses, registrations, compact records, and interpretation
into the canonical checkout. Move unique ignored run directories without changing
their bytes, verify their inventories, and retain archive receipts. Never overwrite
an existing UUID or merge server databases. Keep a worktree while it contains the
only copy of private diagnostics or unintegrated work; do not force-remove it.

The former sibling `research-liquidity-2a25f7c4` is preserved at
`.worktrees/research-liquidity-2a25f7c4`. Its source and public evidence are already
integrated. Its separate server database and private diagnostic logs remain there.
Historical manifests keep their original paths as provenance; all present research
storage is under this canonical repository.

## From source to the site

The notebook source lives only in this repository. Web reads it locally and stages
the allowed documents/assets into `.research-content` during a production build.
Study TOML, skills, raw runs, private state, and nested worktrees are never staged.
See [the release handoff](publishing.md#release-handoff) for the existing branch and
deployment workflow. A local write-up, a source push, and a deployed page are
separate states; report the one actually verified.
