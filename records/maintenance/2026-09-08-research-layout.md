# Research layout consolidation

Moved the linked worktree from `../research-liquidity-2a25f7c4` to
`.worktrees/research-liquidity-2a25f7c4` with `git worktree move`. The branch and
HEAD (`5dd21097fde254e0d49e6929d249e230b4a02394`) are unchanged. The old sibling
path no longer exists. No source, private log, runtime database, or build output
was deleted.

Before moving, the worktree had no source files absent from the canonical
checkout. Differing source files were the newer notebook/tutorial/replay changes
in the canonical checkout. Shared run files were byte-identical. The worktree
also contained private diagnostics absent from the public evidence copies and
a separate server database; those remain inside the retained worktree.

After moving, all 16 canonical run inventories and all 10 retained worktree run
inventories verified. All 16 archive receipts still resolved to files with their
recorded SHA-256. Historical manifests and receipts were not rewritten.

Filed the 14 existing immutable experiment protocols and 16 run records under
`ports/liquidity` and `log/protocol-smoke`. Legacy ownership lives in study TOML,
leaving the original registrations and evidence hashes intact. The notebook
index, approach sections, and roadmap now derive from those study records.

This is repository organization and validation, not a new research experiment.
No source push or site deployment was performed by this maintenance operation.
