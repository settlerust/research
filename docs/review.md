# Code review without result-file noise

`.greptile/config.json` uses Greptile's documented newline-separated gitignore
syntax. It ignores all files, reopens directories for traversal, then includes
only `.rs`, `.ts`, `.tsx`, and `.py` source. Data/build/generated directories are
excluded again. Markdown, MDX, TOML, JSON, JSONL, CSV, locks, and images are not
review targets. They can still provide reviewer context.

`fileChangeLimit` is explicitly 1000 so the previous default of 100 does not gate
ordinary research PRs. Ignore filtering and PR-size gating may occur at different
stages in the hosted service; the configuration does not promise unlimited-size
PRs. Keeping raw data out of Git is the primary fix. The repository check tests
the allowlist with Git's actual ignore matcher, including more than 100 JSON
files alongside nested code.

Install/enable the Greptile GitHub app for the new repository to activate reviews.
That hosted connection cannot be established by a local configuration file.

Reference: [Greptile configuration schema](https://www.greptile.com/docs/code-review/greptile-config-reference).
