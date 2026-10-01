<!-- Ordinary changes: target dev. Start a feature/<slug>, fix/<slug>, improvement/<slug>, chore/<slug>, or similarly named branch from dev; use the same branch name across coordinated repositories. Git branch names do not start with a slash.
For dev -> main releases, use .github/PULL_REQUEST_TEMPLATE/release.md instead.
Replace guidance with actual results. Supply full PR URLs and a brief reason, or explicitly write None. Update links in both directions; do not leave placeholders. -->

## Change

<!-- Explain the policy, experiment, notebook, or publishing change. For evidence changes, link the owning study, registered hypothesis, run IDs, findings, and limitations. -->

## Coordination

Upstream PRs must merge first; downstream PRs depend on this change.

- Upstream: None <!-- Required first: replace None with actual PR URLs when applicable. server/protocol changes for policies; design for newly registered research visuals; arena for imported match evidence when applicable. -->
- Downstream: None <!-- Depends on this change: replace None with actual PR URLs when applicable. web research publication; service/lobby when staged research content or assets change. -->
- Merge/deploy order: <!-- State required order and compatibility between intermediate revisions, or Independent. Shared-stack dispatches can deploy multiple repositories. -->

## Validation

<!-- Report actual commands/results and any checks not run with the reason. Suggested repository checks: `just check`; use `just notebook` and `just site-check` for substantive research/publication changes, and a bounded protocol smoke for policy changes. Preserve actual evidence and archive receipts. -->

- Expected dev target: No independent site deployment. Research pages are published by web at https://dev.settlers.dev/research; hosted consumers may stage research assets.
- Verified result: <!-- Record check results, study/asset revisions, and actual web deployment URL/run for published content. Smoke runs validate behavior, not strategic superiority. Give successful run/preview links and outcomes, or Pending; configured URLs are not proof of deployment. -->
