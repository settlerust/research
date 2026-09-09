---
name: settlers-research-workflow
description: Organize Settlers investigations under an approach or the experiment log, preserve experiment evidence, and keep the published research notebook synchronized. Use when starting, continuing, integrating, or writing up research in this repository.
---

Read `docs/research-workflow.md` for the directory contract and commands, then
`docs/status.md`, `docs/roadmap.md`, and the owning approach before choosing work.
The canonical research checkout owns all research. Temporary worktrees go only in
its ignored `.worktrees/`; never create another `../research-SLUG` directory.
`just worktree NAME` resolves this location even from a linked worktree and refuses
to silently start from a checkout with uncommitted changes.

Before implementing, find the existing study in `approaches/*/studies/*.toml` or
`log/studies/*.toml`. Create one with `just study APPROACH/SLUG --title ...
--question ...` when the question is distinct. Use `log/SLUG` for protocol,
benchmarking, or other cross-cutting investigations. One study owns each report
and protocol; link related approaches instead of duplicating evidence. A new
follow-up gets a new study, preserving the completed study's decision.

Use `settlers-experiment` for the experiment itself. Pass `--study OWNER/SLUG`
to every registration and to candidate-specific smoke matches. Plain `just match`
files infrastructure smokes in `log/protocol-smoke`. Never edit a completed
registration to move it: `legacy_experiments` is the migration mapping for old
protocols that predate study ownership.

After a run or meaningful interpretation, retain all outcomes and update the
study's `updated`, `status`, `outcome`, `next_step`, and actual `attribution`.
Append the dated daily log, including failures and run IDs (an exhaustive linked
audit can carry the IDs). Add its path to `logs`. Add public findings to `reports`
using `settlers-publishing`, and put their paths in the study's `reports` array.
Manually revise the approach explanation and `docs/status.md` if the evidence
boundary changes. Maintenance alone does not need a fictitious research result.

Run `just notebook` to refresh the experiment index and generated sections of the
approach pages and roadmap. Never hand-edit those generated sections. Run
`just check` and `just site-check` when web is available. These fail on unfiled
protocols/reports, undocumented retained runs, broken study references, and stale
generated pages. Integrate source, registrations, compact records, study metadata,
dated interpretation, and public exhibits as one reviewable change.

For site publication, follow the existing `service` release workflow described in
`docs/publishing.md`. Use any commit/push/deploy authority already given by the
user; this skill adds no approval step or deployment authority. Distinguish local
validation, pushed source, and a verified deployed page in the handoff. Research
is unfinished if the claimed result is still only in an agent's temporary worktree.
