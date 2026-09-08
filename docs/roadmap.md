# A plan for a stronger player

## Establish a trustworthy baseline

First measure the existing fast and ETA builders in a fixed, seat-balanced
lineup. Check completion, invalid actions, turn count, and points before comparing
win rates. Inspect a few public replays to understand failure modes. Record a
negative or inconclusive finding with the same care as an improvement.

## Improve the value of a build

Opening production is a starting point. Add resource diversity, access to grain
and ore, port conversion, and reachable settlement sites. During play, estimate
how long the current hand and production need to fund a useful build. Compare
that estimate with the opportunity cost of a road or development card.

## Model uncertainty and opponents

Track a belief over unseen resource and development cards using only visible
production, trades, expenditures, discards, and counts. Test calibration on
separate diagnostic data before relying on it in search. Beliefs must remain
consistent with a player's own observation; a public replay is not an oracle.

## Search a small set of useful plans

Compare short build sequences, blocked routes, award races, and trade choices.
Use belief samples for hidden information and chance branches for dice. Start
with a strict decision budget and test whether better planning survives protocol
latency. The pure Rust engine has offline chance hooks, but a fair policy must
construct its simulated states from its own information.

## Learn and evaluate

Use self-play or retained development games to learn a value function or rank
candidate plans. Freeze a model and evaluate it against diverse opponents on
fresh games. Include strategy ablations: production only, planning without
beliefs, and negotiation disabled. A higher score against one weak opponent does
not establish general strength or optimal play.
