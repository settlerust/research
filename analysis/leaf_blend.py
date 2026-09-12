"""Blend-arm diagnostics from engine-arena swapped pairs: the seating-corrected effect of
each pair (per-seed half-difference of the two slot-0-minus-slot-1 contrasts and the seating
term, their half-sum), a pooled estimate over any number of pairs named as after-the-fact
pooling, and per-arm play statistics (wins, mean points, mean decision time, builds,
development cards, trades, discards). The candidate sits in slot 0 in the first half of a
pair and slot 1 in the second."""
import argparse
import json
import math
from pathlib import Path

BUILD_KEYS = ['settlements_built', 'cities_built', 'roads_built', 'development_bought',
               'player_trades', 'offers', 'counters', 'counters_accepted', 'declined',
               'cards_discarded', 'knights_played']


def rows(path):
    out = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    done = [r for r in out if r['game'].get('status') == 'completed']
    return out, done


def per_seed(done, slots=(0, 1)):
    by = {}
    for r in done:
        by.setdefault(r['seed'], []).append(r['winner_slot'])
    return {s: (sum(1 for w in ws if w == slots[0]) - sum(1 for w in ws if w == slots[1])) / len(ws)
            for s, ws in by.items()}


def interval(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def pair_effect(a_path, b_path):
    all_a, done_a = rows(a_path)
    all_b, done_b = rows(b_path)
    da, db = per_seed(done_a), per_seed(done_b)
    if set(da) != set(db):
        raise SystemExit(f'{a_path} and {b_path} must play the same seeds')
    effects = {s: (da[s] - db[s]) / 2 for s in da}
    seating = {s: (da[s] + db[s]) / 2 for s in da}
    mean, lo, hi = interval(list(effects.values()))
    seat, slo, shi = interval(list(seating.values()))
    return {'attempts': (len(all_a), len(all_b)), 'completed': (len(done_a), len(done_b)),
            'effect': (mean, lo, hi), 'seating': (seat, slo, shi),
            'effects': effects, 'seeds': len(da)}


def arm_stats(a_path, b_path):
    """Candidate (slot 0 in half A, slot 1 in half B) against the control, over completed games."""
    stats = {}
    for name, path, cand, ctrl in (('candidate', a_path, 0, 1), ('control', b_path, 1, 0)):
        _, done = rows(path)
        recs = [r['game']['seats'][r['slots'].index(cand)] for r in done]
        c_rec = [r['game']['seats'][r['slots'].index(ctrl)] for r in done]
        decisions = sum(s['decisions'] for s in recs)
        stats[name] = {
            'games': len(recs),
            'wins': sum(r['winner_slot'] == r['slots'].index(cand) for r in done),
            'mean_points': sum(s['points'] for s in recs) / len(recs),
            'mean_points_control': sum(s['points'] for s in c_rec) / len(c_rec),
            'mean_decision_ms': sum(s['decision_ms'] for s in recs) / decisions if decisions else None,
            **{k: sum(s.get(k, 0) for s in recs) / len(recs) for k in BUILD_KEYS},
        }
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair', nargs=3, action='append', metavar=('LABEL', 'HALF_A', 'HALF_B'),
                        help='label, games.jsonl with the candidate in slot 0, games.jsonl with it in slot 1')
    args = parser.parse_args()
    pooled = []
    for label, a, b in args.pair:
        p = pair_effect(a, b)
        mean, lo, hi = p['effect']
        seat, slo, shi = p['seating']
        print(f'{label}: seeds {p["seeds"]}, games {p["completed"][0]} and {p["completed"][1]} completed '
              f'({p["attempts"][0]} and {p["attempts"][1]} attempted)')
        print(f'  effect {mean:+.3f} wins per game (95% interval {lo:+.3f} to {hi:+.3f}); '
              f'seating term {seat:+.3f} ({slo:+.3f} to {shi:+.3f})')
        pooled += list(p['effects'].values())
        s = arm_stats(a, b)
        c, k = s['candidate'], s['control']
        print(f"  candidate: {c['wins']}/{c['games']} wins, points {c['mean_points']:.2f} vs {c['mean_points_control']:.2f}, "
              f"decision {c['mean_decision_ms']:.0f} ms, cities {c['cities_built']:.2f}, dev {c['development_bought']:.2f}, "
              f"settlements {c['settlements_built']:.2f}, roads {c['roads_built']:.2f}, trades {c['player_trades']:.2f}, "
              f"counters {c['counters']:.2f}, declines {c['declined']:.2f}, discards {c['cards_discarded']:.2f}")
        print(f"  control:   {k['wins']}/{k['games']} wins, points {k['mean_points']:.2f} vs {k['mean_points_control']:.2f}, "
              f"decision {k['mean_decision_ms']:.0f} ms, cities {k['cities_built']:.2f}, dev {k['development_bought']:.2f}, "
              f"settlements {k['settlements_built']:.2f}, roads {k['roads_built']:.2f}, trades {k['player_trades']:.2f}, "
              f"counters {k['counters']:.2f}, declines {k['declined']:.2f}, discards {k['cards_discarded']:.2f}")
    if len(args.pair) > 1 and pooled:
        mean, lo, hi = interval(pooled)
        print(f'pooled after-the-fact over {len(pooled)} seeds: effect {mean:+.3f} '
              f'(95% interval {lo:+.3f} to {hi:+.3f})')


if __name__ == '__main__':
    main()
