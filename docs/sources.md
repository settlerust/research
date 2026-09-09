---
title: Rules and reading guide
summary: Primary references for Catan, strategic communication, hidden-information search, and language-guided planning.
---

# Rules and reading guide

These sources motivate the research program. None establishes a local ranking among the proposed policies. Distinguish a game rule, a result from another experimental setting, and an original hypothesis in this notebook.

| Source | What it contributes | Boundary of the evidence |
| --- | --- | --- |
| [CATAN base-game rules and almanac, 2020 edition](https://www.catan.com/sites/default/files/2021-06/catan_base_rules_2020_200707.pdf) | Reference rules for production, trading, building, development, and victory | The arena’s versioned server protocol determines the implemented rules; expansions and house rules are outside this program |
| [Crawford & Sobel, Strategic Information Transmission, 1982](https://www.haverford.edu/sites/default/files/CrawfordSobel1982.pdf) | A formal model in which partially aligned interests can support informative communication | Its equilibrium analysis is not a solved strategy for a four-player Catan table |
| [Keizer et al., Evaluating Persuasion Strategies and Deep Reinforcement Learning methods for Negotiation Dialogue agents, 2017](https://aclanthology.org/E17-2077/) | Direct Catan research comparing dialogue negotiation strategies in human-versus-bot games | The study’s interface, participants, policies, and training differ from this arena; it motivates replication, not an imported win-rate claim |
| [Cowling, Powley & Whitehouse, Information Set Monte Carlo Tree Search, 2012](https://eprints.whiterose.ac.uk/id/eprint/75048/) | Search methods that represent hidden information and avoid some weaknesses of determinization | Better results in its tested domains do not demonstrate strength in this implementation of Catan |
| [Meta FAIR, CICERO research and materials, 2022](https://ai.meta.com/research/cicero/) | An example of integrating language with strategic planning in Diplomacy | Diplomacy’s communication and action structure differ substantially; this is an architectural analogy |

Read the Catan negotiation paper alongside [truthful signals](../approaches/signals/README.mdx), the communication model alongside [bluffs and disclosure](../approaches/deception/README.mdx), and the information-set paper alongside [search under uncertainty](../approaches/search/README.mdx).

The reputation, pliability, and containment studies are original proposed comparisons informed by general incentive reasoning. Their teaching diagrams and toy calculations are not published experimental findings. The sources were checked on September 8, 2026.
