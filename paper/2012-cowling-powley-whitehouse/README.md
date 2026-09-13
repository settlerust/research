# Information Set Monte Carlo Tree Search for Settlers expectimax

This article explains Cowling, Powley, and Whitehouse's 2012 paper, [Information Set Monte Carlo Tree Search](./CowlingPowleyWhitehouse2012.pdf), and translates its ideas into the vocabulary of the Settlers engine. The paper's primary result is a family of Monte Carlo tree search algorithms for games with hidden information, stochastic events, and partially observable moves. Its central design choice is simple:

> Search a tree of information sets, not one independent perfect-information tree for every hidden-world sample.

That choice is directly relevant to Settlers. A seated player sees its own hand and the public board, but not opponents' resource or development hands. The current [tunable expectimax search](../../../server/docs/expectimax.md#the-tunable-search-expectimax-v2) already samples hidden worlds and shares the root decision across worlds with the same seat observation. This paper gives the formal explanation for why that sharing matters, identifies where a determinized search can still make invalid decisions, and suggests a path toward better opponent models when the fixed builder becomes the limiting approximation.

This is a design translation, not evidence that ISMCTS is stronger in Settlers. The paper evaluates Lord of the Rings: The Confrontation, Phantom (4,4,4), and Dou Di Zhu. None of those results should be treated as a Settlers result.

## The paper in one page

In an imperfect-information game, a player acts from an information set: a set of underlying states that are indistinguishable to that player. A determinization samples one hidden state from the current information set, reveals it to the search, and runs a perfect-information solver on that sample. Repeating this for many samples is useful, but it has three structural problems:

1. **Strategy fusion.** Separate determinizations can choose different actions from states that the player cannot distinguish. The resulting policy is not executable by the real player.
2. **Nonlocality.** A determinization may contain a state that other players can make likely or unlikely through their actions. Averaging independent perfect-information searches does not model that reachability correctly.
3. **Budget fragmentation.** Independent trees duplicate work in regions that are equivalent from the acting player's point of view. A shared information-set tree can spend the whole budget on common structure.

The paper proposes three related algorithms:

- **SO-ISMCTS:** one tree from the root player's point of view. Nodes represent the root player's information sets and edges represent actions.
- **SO-ISMCTS+POM:** an SO tree whose edges represent moves as observed by the root player, rather than the hidden actions that caused those observations. This handles partially observable moves, but uses a weak random model for opponent actions that look identical to the root player.
- **MO-ISMCTS:** one information-set tree per player. Each simulation uses a sampled determinization to select legal actions, but selection statistics are taken from the tree belonging to the player who is acting. Every player's tree is advanced using that player's observation of the simulated move.

The paper's experiments find the largest gains where strategy fusion is harmful or where a deeper shared tree is more valuable than many shallow determinizations. It reports that the variants are roughly on par with determinized UCT in Dou Di Zhu, where the union of legal actions across hidden states creates a very large branching factor. That tradeoff is important for Settlers: information-set sharing is valuable, but a node that represents many possible hands can have more candidate actions than any one determinization.

## Settlers terminology map

The following mapping is the minimum vocabulary needed to apply the paper to this repository.

| Paper concept | Settlers interpretation |
| --- | --- |
| Full state `s` | A complete engine `State`, including every player's hands, the development deck composition, and the current phase. |
| Observation | The seated player's redacted `GameView` plus its redacted event history. |
| Information set `I_p` | All full states consistent with seat `p`'s observation and remembered history. |
| Determinization | A sampled `State` from that information set. The current sampler constrains resource hands and development counts from public knowledge and history. |
| Action | A rule command such as `Roll`, `BuildRoad`, `BuyDevelopment`, `MoveRobber`, or `Trade`. |
| Move | What a particular observer can distinguish about an action and its result. In ordinary Settlers most commands are publicly named, but their private hand effects are not visible to every seat. |
| Environment player | Dice, development-card draws, robber theft, and other chance resolution. |
| Information-set node | A search node keyed by what one observer can know, not by the hidden full state. |
| Availability count | The number of sampled worlds in which a candidate action was legal at an information-set node. |

The distinction between **state** and **information set** is essential. If two sampled worlds have different opponent hands but the same observation for the root seat, they should not allow the root policy to choose two different current actions merely because the search saw the hidden hands. They are two members of one root information set.

## What current expectimax already gets right

The current v2 search is not ISMCTS, but several parts of its architecture already implement the paper's most important invariant.

### World sampling is belief input, not a decision key

`sampling::worlds` constructs several complete worlds from the player's redacted observation and `ResourceKnowledge`. It uses public bank counts, hand totals, bounds inferred from history, known development-card counts, and the player's exact hand. This is better than the paper's uniform-determinization assumption when the history supplies useful constraints, but it is still an approximation to a posterior distribution.

The sampled worlds should be treated as weighted belief support:

```text
worlds = [(s_1, w_1), (s_2, w_2), ...]
sum(w_i) = 1
```

The weights are probabilities or sampling weights for evaluating uncertainty. They are not permission to make a different root decision in every world.

### `regroup` is the information-set operation

The v2 search applies an action or chance outcome to the sampled worlds and then groups them with `information_set(state, seat)`. The group key contains the board, own hand and development cards, public counts, bank, deck count, robber, awards, phase, and turn. It deliberately excludes hidden opponent hands, hidden deck composition, and the random cursor. See the implementation in [`v2/key.rs`](../../../server/crates/expectimax/src/v2/key.rs).

Within a group, `best_line` selects one root-seat action and applies it to every compatible world. That is the expectimax analogue of sharing an information-set node. The corrected search report documents why this matters: the current search takes a maximum over the player's own continuations and an expectation over chance, instead of averaging unrelated action sequences. See [After the fix: half the games on paired boards](../../reports/expectimax-v2-corrected.mdx).

### Exact chance branches and common scenarios are complementary

The v2 search branches exactly over the player's own dice roll, development-card purchase outcomes, and robber theft outcomes when those branches are represented by a manageable distribution. Between planned turns it uses common random dice scenarios for all candidates, which pairs their estimates and reduces comparison noise. This is a different engineering choice from MCTS rollouts, but it serves the same purpose: represent uncertainty without letting each candidate receive a different random future.

### The transposition key is already an observer key

The v2 transposition tables merge positions that look the same to the root seat. The [transposition report](../../reports/transpositions.mdx) describes the key and its three cache lifetimes. That is conceptually close to the shared information-set statistics in ISMCTS.

There is one important limitation. The current key describes the current observation, not the entire belief distribution that produced it. Two histories can sometimes have the same visible board and counts while implying different hidden-hand beliefs. A future belief-aware cache would need either a belief signature in its key or a lifetime that guarantees the belief model has not changed. Reusing a value across sampled hands is safe only as an approximation whose error is measured, not as a proof that the worlds are interchangeable.

## Where the paper exposes remaining expectimax risks

### Determinization can still fuse impossible strategies

Suppose two worlds are identical to the root seat except that one opponent holds more ore and the other holds more grain. A perfect-information solver can choose different root actions in those worlds because it sees the opponent's hand. A real Settlers player cannot do that. Averaging the two action values after each solver has made its private choice is strategy fusion.

The current v2 root decision avoids this at the current information set by applying one action to a grouped set of worlds. The risk returns if a new feature evaluates each hidden world with an independent root policy, or if an opponent model is allowed to condition on hidden information that its own observation does not contain. The safe rule is:

```text
same observer + same observation + same belief context
    -> one policy node and one action distribution
```

The rule applies to every player, not only to the root seat.

### Hidden hands affect reachability, not only leaf value

A hidden hand changes which actions an opponent can take, which actions they prefer, and which states are reached next. A solver that only samples hands and averages leaf values can miss this action-dependent reachability. The paper calls the broader issue nonlocality.

The current v2 search partially addresses it by running the fixed builder on each sampled hand and by using the same scenarios for every candidate. That is a useful behavioral approximation, but it is not a search over the opponent's information set. The builder is allowed to read the sampled opponent hand because it is modeling that opponent's private observation; the root player still does not get to see that hand. If the model of opponent behavior is wrong, more root search does not fix it.

### Information-set nodes have subset-armed action sets

At an opponent node, the union of legal actions over all compatible worlds can be much larger than the legal action set in any one world. A candidate action can be legal in only a small fraction of visits. Ordinary UCB statistics treat that rare action as if it had been available on every parent visit, which over-explores it.

The paper calls this a **subset-armed bandit**. For each information-set node and action, maintain at least:

```text
N(I, a)  = selections of a
A(I, a)  = compatible visits on which a was available
W(I, a)  = accumulated reward when a was selected
```

Use `A(I,a)` in the exploration calculation where ordinary UCB would use the parent visit count, and increment availability for every sibling legal in the sampled determinization, not only for the selected action. This is required if Settlers gains a true information-set tree for opponent decisions.

## Which ISMCTS variant maps to Settlers?

### SO-ISMCTS is a useful diagnostic, not the final model

SO-ISMCTS is the smallest change from a root search. It would maintain one tree keyed by the root seat's observation and use a sampled world to filter legal actions during each simulation. It is useful for a controlled comparison against the current expectimax because it shares information across sampled worlds and has a relatively small memory footprint.

Its opponent assumption is pessimistic: because the tree is built from the root player's viewpoint, it can effectively let an opponent condition on distinctions the root player cannot observe. In Settlers this can make an opponent appear to know the exact root player's hidden hand or the exact hidden cards behind a public count. SO-ISMCTS should therefore be treated as a diagnostic baseline or as a deliberate worst-case opponent model.

### SO-ISMCTS+POM is usually not needed for base Settlers

The POM variant merges opponent actions that the root observer cannot distinguish. It is appropriate when an opponent's action identity is hidden but its consequence is partially observed, as in the paper's LOTR:C movement example.

Base Settlers is turn-based and normally exposes the command and public result. Hidden resource ownership is hidden state, not usually a partially observable action identity. Dice, draws, theft, and discards are chance or private-outcome events. Do not add POM merely because hands are hidden. Add it only if the protocol or a future variant introduces a move whose identity is genuinely unobservable to another player.

### MO-ISMCTS is the principled extension

MO-ISMCTS maintains one tree per observer. At a simulated state, the tree used for action selection belongs to the player who is about to act. The action is legal only if it is legal in the sampled world, but its statistics are shared across worlds that are indistinguishable to that acting player. After the action, every observer's tree advances along the move or observation that that observer would receive.

This is the closest match to a Settlers opponent model:

- the root tree cannot condition on opponents' private hands;
- an opponent tree can condition on that opponent's own hand;
- nonparticipants use only the public event and their own private update;
- chance outcomes update the public and private observations separately;
- action statistics are shared across compatible hidden worlds.

MO-ISMCTS is not a Nash-equilibrium solver. It still needs a rollout policy, a belief sampler, a reward model, and a rule for how the opponent behaves when its search is shallow. Its advantage is that the policy is represented in the correct observer's information space.

## A Settlers implementation plan

The safest integration is a hybrid, because the current expectimax has exact domain logic that should not be discarded.

### 1. Preserve the current belief and rule layers

Keep `ResourceKnowledge`, history-conditioned hand sampling, exact engine chance outcomes, and the public/private observation boundary. Do not pass the research spectator projection or another player's hidden hand into a seated policy. The relevant input contract is documented in [`server/docs/expectimax.md`](../../../server/docs/expectimax.md#inputs-and-public-resource-knowledge).

### 2. Add an information-set tree as a bounded opponent model

Represent a node as:

```text
InfoNode {
    observer: Seat,
    observation_key: ObservationKey,
    children: Map<ObservedMove, EdgeStats>,
}

EdgeStats {
    visits: u64,
    availability: u64,
    total_value: f64,
}
```

`ObservationKey` should be derived from the observer's protocol-visible state and relevant history or belief signature. The existing [`information_set`](../../../server/crates/expectimax/src/v2/key.rs) function is a useful starting point for the current-state portion, but it is not automatically a complete history-dependent belief key.

### 3. Use sampled worlds only to restrict a simulation

For each iteration:

```text
world <- sample a hidden world from the root belief
state <- current public/private full state represented by world

while state is nonterminal and tree is not expanded:
    p <- player to act in state
    node <- tree[p][observation of p in state]
    legal <- actions legal in this sampled world
    action <- bandit selection among legal children
    increment availability for every legal sibling in node
    state <- apply action and chance outcome
    advance every observer tree using that observer's observation

roll out with a bounded policy
backpropagate root-relative reward along all observed nodes
return the most visited root action
```

The critical detail is that the same sampled world restricts legality for one simulation, while the node statistics are shared across all worlds that map to the same observer information set. Never create a separate root child merely because the hidden world changed.

### 4. Keep chance semantics explicit

Settlers dice are not uniformly distributed over totals. The exact probabilities are the 36 ordered dice pairs. Development draws and robber thefts also have count-weighted outcomes. An MCTS implementation may sample these outcomes, but it must sample from the correct distribution. For low-branching events, exact branching is often preferable and can reuse the current `step` implementation. For large or repeated branches, outcome sampling can be paired with common random numbers so candidate comparisons remain low variance.

### 5. Decide what reward is being backed up

The current v2 leaf is an additive heuristic with terms for points, hand, production, planning, expansion, development, risk, ports, road progress, and opponent progress. Those terms are useful for Settlers expectimax but are not probabilities of winning. An ISMCTS experiment must state whether it backs up:

- terminal win/loss only;
- the current v2 heuristic at a fixed horizon;
- a blended terminal and heuristic reward; or
- a learned leaf such as the [n-tuple evaluator](../../reports/ntuple-leaf.mdx).

The reward perspective must be explicit. For a root decision, convert every rollout outcome to the root seat's utility. For an opponent tree, either back up the opponent's own utility during its action selection or use a documented shared utility model. Mixing those perspectives silently produces an incoherent policy.

## Recommended research sequence

The paper suggests a testable progression rather than an immediate replacement of the baseline.

1. **Fixture:** Build a small hidden-resource fixture in which two worlds have the same root observation but require one common robust action. Verify that per-determinization search chooses the wrong fused policy and an information-set node does not.
2. **Diagnostic PIMC:** Add a determinized UCT or rollout baseline using the existing `sampling::worlds`, with the same leaf and equal transition budget as expectimax. Measure action agreement, tree depth, and repeated work before measuring wins.
3. **SO-ISMCTS:** Share root statistics across sampled worlds. Implement availability counts and compare against the diagnostic PIMC baseline. This isolates strategy-fusion and budget-sharing effects.
4. **MO-ISMCTS opponent model:** Add one tree per seat, starting with public actions and private hand updates. Compare the fixed builder, SO-ISMCTS, and MO-ISMCTS as opponent models inside the same root expectimax.
5. **Belief and nonlocality:** Add history-dependent belief updates only after the tree and observation keys are correct. A better posterior changes the probability of worlds; it must not be confused with changing the leaf value or with socially reranking an action.
6. **Registered arena comparison:** Use the research [experiment program](../../docs/experiment-program.md), paired deterministic boards, equal transition or wall-clock budgets, and a fixed opponent lineup. Report failures and incomplete games beside the completed denominator.

Useful diagnostics include:

- root-action changes between determinization and information-set search;
- the fraction of worlds in which each action is legal;
- `availability` versus `visits` for rare actions;
- unique information-set nodes versus full-state nodes;
- rollout transitions per decision and completed search depth;
- cache hits and whether a cache key includes belief context;
- performance on hidden-information fixtures designed to trigger strategy fusion.

## What not to copy from the paper

The paper's algorithms are a foundation, not a list of Settlers defaults.

- Do not copy its uniform determinization distribution when history and public bank counts provide stronger constraints.
- Do not copy its UCB constant as a settled Settlers hyperparameter. Bandit constants are search and reward-scale dependent.
- Do not use EXP3 just because the paper discusses simultaneous moves. Base Settlers has no ordinary simultaneous action phase.
- Do not interpret MO-ISMCTS as equilibrium computation. The paper explicitly distinguishes strong practical play from Nash solving.
- Do not assume deeper information-set search always wins. The paper's Dou Di Zhu result shows that the union of legal actions can erase the depth and budget advantage.
- Do not treat the paper's win rates as evidence for this repository. A Settlers comparison must be registered and run under the local evidence contract.

## Bottom line

The paper's most important lesson for Settlers expectimax is a policy constraint:

> A player may condition its action only on information available to that player.

The current v2 search already enforces this for the root action by regrouping sampled worlds by the root information set. The next useful application is opponent modeling. A fixed builder is fast and reproducible, but it does not learn a shared policy over an opponent's information set. SO-ISMCTS can provide a controlled diagnostic; MO-ISMCTS is the better conceptual target when the goal is for every seat to act from its own observation. Subset-armed availability counts, observer-correct transition keys, explicit chance probabilities, and belief-aware cache lifetimes are the implementation details that determine whether that target is real or only a determinized search with a new name.

## Primary source

Cowling, Peter I., Edward J. Powley, and Daniel Whitehouse. “Information Set Monte Carlo Tree Search.” *IEEE Transactions on Computational Intelligence and AI in Games*, vol. 4, no. 2, 2012, pp. 120-143. The repository copy is the [submitted paper PDF](./CowlingPowleyWhitehouse2012.pdf); the bibliographic record and publisher DOI are available from the [White Rose Research Online record](https://eprints.whiterose.ac.uk/id/eprint/75048/) and [IEEE DOI](https://doi.org/10.1109/TCIAIG.2012.2200894).
