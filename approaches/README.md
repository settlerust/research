# General approaches

| Approach | Mechanism to test | Main failure to watch |
| --- | --- | --- |
| Production and expansion | Prefer productive, diverse intersections and reachable sites | Resources accumulate without a route to points |
| Acquisition-time planning | Rank builds by expected time to afford them | A short estimate ignores blocking and opponent races |
| Belief-based search | Sample hidden hands compatible with public evidence | Hidden-state leakage or poorly calibrated beliefs |
| Negotiation | Price trades by both players' build opportunities | Helping a leader or learning network scheduling quirks |
| Learned value and self-play | Learn which plans lead to wins against varied opponents | Overfitting to a narrow opponent pool |

The registered `fast` and `eta` opponents come from the server's Rust policy
crate. `legal-first` is a small research-owned Python protocol example, intended
for plumbing and legality checks. It is not presented as a competitive baseline.

Put a new policy in `policies/<name>/` and add its command to the registry. Put
its explanation and findings under `approaches/<name>/README.mdx`, with links to
the preregistered experiment and run records. Shared mechanics belong in a
policy-independent module only when more than one policy needs them.
