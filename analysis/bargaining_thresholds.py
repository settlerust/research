"""How large a swap is in each leaf's currency, read from a traced engine-arena screen.

The bargaining thresholds are fixed numbers: the trade margin ((1 - trade) * 24, 12 at the
default slider), a threat premium of up to 30 on that margin, and a partner-gain cost priced with
the hand-written card and point values. A trace records, for every search decision, the top
candidates with their value contributions; a proposal or counter row carries the value of the
accepted continuation and of the best plain alternative, so their difference is the gross gain
of the swap before any threshold, in the seat's own leaf units. This script prints that
distribution per slot, the spread of plain candidate values per decision, and how often the
margin alone would have blocked a swap the lookahead liked.

    python3 analysis/bargaining_thresholds.py runs/screens-bargaining-tables/trace-l1-tables-hand.jsonl
"""
import argparse
import json
import statistics
from collections import defaultdict


def kind(candidate):
    command = candidate.get('command') or {}
    note = candidate.get('note') or ''
    if command.get('type') == 'offer_trade':
        return 'counter' if note.startswith('counter to') else 'offer'
    if command.get('type') == 'accept_trade':
        return 'accept'
    if command.get('type') == 'reject_trade':
        return 'decline'
    return 'plain'


def quantiles(values):
    if not values:
        return None
    xs = sorted(values)
    q = statistics.quantiles(xs, n=4) if len(xs) >= 4 else [xs[0], xs[len(xs) // 2], xs[-1]]
    return {'n': len(xs), 'median': q[1], 'q1': q[0], 'q3': q[2], 'mean': statistics.fmean(xs)}


def fmt(q):
    if not q:
        return 'none'
    return f"n={q['n']:5d} median {q['median']:7.1f} (q1 {q['q1']:7.1f}, q3 {q['q3']:7.1f}) mean {q['mean']:7.1f}"


def analyse(paths, margin):
    gross = defaultdict(lambda: defaultdict(list))   # slot -> kind -> gross gains
    spread = defaultdict(list)                       # slot -> per-decision spread of plain values
    scale = defaultdict(list)                        # slot -> best plain value per decision
    chosen = defaultdict(lambda: defaultdict(int))   # slot -> kind chosen
    decisions = defaultdict(int)
    blocked = defaultdict(lambda: [0, 0])            # slot -> [liked swaps, of which the margin alone blocks]
    accept_gap = defaultdict(list)                   # slot -> accept value minus wait value, thresholds removed
    accepts = defaultdict(lambda: defaultdict(int))  # slot -> accepts the lookahead liked and what blocked them
    premiums = defaultdict(list)                     # slot -> threat premium plus partner cost on priced accepts
    for path in paths:
        for line in open(path):
            if not line.strip():
                continue
            row = json.loads(line)
            slots = row['slots']
            for entry in row['game'].get('trace') or []:
                if entry.get('phase', {}).get('type') != 'main':
                    continue
                slot = slots[entry['seat']]
                candidates = entry.get('candidates') or []
                if not candidates:
                    continue
                decisions[slot] += 1
                plain = [c['value'] for c in candidates if kind(c) == 'plain']
                if plain:
                    spread[slot].append(max(plain) - min(plain))
                    scale[slot].append(max(plain))
                waits = [c['value'] for c in candidates if kind(c) in ('plain', 'decline')
                         and (c.get('action') or {}).get('type') == 'end_turn']
                chosen_command = entry.get('chosen') or {}
                chosen_kind = 'plain'
                for c in candidates:
                    if c.get('command') == chosen_command:
                        chosen_kind = kind(c)
                        break
                chosen[slot][chosen_kind] += 1
                for c in candidates:
                    k = kind(c)
                    contributions = c.get('contributions') or {}
                    if k in ('offer', 'counter') and c.get('trade'):
                        t = c['trade']
                        if t.get('accepted_value') is None or t.get('rejected_value') is None:
                            continue
                        gain = t['accepted_value'] - t['rejected_value']
                        gross[slot][k].append(gain)
                        if k == 'offer' and gain > 0:
                            blocked[slot][0] += 1
                            # The offer's value is plain + p*(accepted - plain) - margin - threat cost;
                            # the margin alone blocks it when p*gain is below the plain margin.
                            expected = contributions.get('expected')
                            if expected is not None and expected - t['rejected_value'] < margin:
                                blocked[slot][1] += 1
                    elif k == 'accept' and waits:
                        margin_term = contributions.get('trade_margin', 0.0)
                        threat_term = contributions.get('partner_threat', 0.0)
                        stripped = c['value'] - margin_term - threat_term
                        gap = stripped - max(waits)
                        accept_gap[slot].append(gap)
                        if gap > 0:
                            accepts[slot]['liked'] += 1
                            if c['value'] <= max(waits):
                                accepts[slot]['blocked'] += 1
                                # Which threshold did it: the plain margin alone, or only with
                                # the threat premium and the partner cost on top.
                                if gap <= margin:
                                    accepts[slot]['by_margin'] += 1
                                else:
                                    accepts[slot]['by_threat'] += 1
                        premium = -margin_term - margin
                        if premium > 0.5:
                            accepts[slot]['priced'] += 1
                            premiums[slot].append(premium - threat_term)
    return gross, spread, scale, chosen, decisions, blocked, accept_gap, accepts, premiums


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('traces', nargs='+')
    parser.add_argument('--margin', type=float, default=12.0)
    args = parser.parse_args()
    gross, spread, scale, chosen, decisions, blocked, accept_gap, accepts, premiums = analyse(args.traces, args.margin)
    for slot in sorted(decisions):
        print(f"slot {slot}: {decisions[slot]} main-phase decisions; chosen "
              + ', '.join(f"{k} {v}" for k, v in sorted(chosen[slot].items())))
        print(f"  best plain value per decision     {fmt(quantiles(scale[slot]))}")
        print(f"  spread of plain candidates        {fmt(quantiles(spread[slot]))}")
        print(f"  gross gain of a proposal          {fmt(quantiles(gross[slot]['offer']))}")
        print(f"  gross gain of a counter           {fmt(quantiles(gross[slot]['counter']))}")
        print(f"  accept minus wait (no thresholds) {fmt(quantiles(accept_gap[slot]))}")
        liked, cut = blocked[slot]
        if liked:
            print(f"  proposals with positive gross gain {liked}, of which the plain margin of {args.margin:g} "
                  f"blocks {cut} ({cut / liked:.0%})")
        a = accepts[slot]
        if a['liked']:
            print(f"  accepts the lookahead liked {a['liked']}, blocked by the thresholds {a['blocked']} "
                  f"({a['blocked'] / a['liked']:.0%}): by the plain margin {a['by_margin']}, only with the threat "
                  f"premium and partner cost {a['by_threat']}")
        if a['priced']:
            print(f"  accepts priced by a threat {a['priced']}; premium plus partner cost {fmt(quantiles(premiums[slot]))}")


if __name__ == '__main__':
    main()
