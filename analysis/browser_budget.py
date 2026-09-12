"""Browser-budget study: derive the node budget one second of WASM affords from a rate
measurement, read the equal-budget swapped pairs with their depth-completion shares and
decision times, and write the plot assets.

  python3 analysis/browser_budget.py rate RATE.json --asset search-rate-wasm
  python3 analysis/browser_budget.py pairs PAIRS.json [--pool] [--out TABLE.json] [--asset browser-budget-contrasts]
  python3 analysis/browser_budget.py budget BUDGET.json

RATE.json and BUDGET.json come from `analysis/browser_budget_wasm.mjs`; PAIRS.json lists
arms as {"label", "stage", "half_a": RUN, "half_b": RUN} with the candidate in slot 0 of
half A and slot 1 of half B."""
import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analysis.seating_pair import interval, per_seed  # noqa: E402
from harness.records import write_json  # noqa: E402


def quantile(values, q):
    values = sorted(values)
    k = (len(values) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def rate(args):
    data = json.loads(Path(args.rate).read_text())
    rows = [r for r in data['results'] if not r['aborted']]
    labels = list(dict.fromkeys(r['label'] for r in rows))
    out = {}
    series = []
    for key, name in [('wallMs', 'Wall clock'), ('cpuMs', 'CPU time')]:
        points = []
        for i, label in enumerate(labels):
            per_ms = [r['transitions'] / max(r[key], 0.01) for r in rows if r['label'] == label]
            ms = [r[key] for r in rows if r['label'] == label]
            out[f'{label} {key}'] = {
                'views': len(per_ms),
                'median_ms': statistics.median(ms), 'p10_ms': quantile(ms, .1), 'p90_ms': quantile(ms, .9),
                'transitions_per_ms': {'p10': quantile(per_ms, .1), 'p25': quantile(per_ms, .25),
                                       'median': statistics.median(per_ms), 'p75': quantile(per_ms, .75), 'p90': quantile(per_ms, .9)},
                'budget_for_1s': {'p25': round(quantile(per_ms, .25) * 1000), 'median': round(statistics.median(per_ms) * 1000)},
            }
            points.append({'x': i, 'y': round(statistics.median(per_ms), 1),
                           'low': round(quantile(per_ms, .1), 1), 'high': round(quantile(per_ms, .9), 1)})
        series.append({'label': f'WASM in Node, {name.lower()}', 'points': points})
    transitions = {label: statistics.median([r['transitions'] for r in rows if r['label'] == label]) for label in labels}
    out['median_transitions'] = transitions
    top = max(p['high'] for s in series for p in s['points'])
    asset = {'schema': 1, 'kind': 'plot', 'variant': 'bar', 'title': 'Search speed in WASM',
             'evidence': 'measured', 'source': args.source,
             'caption': args.caption,
             'x': {'label': 'Search', 'min': 0, 'max': len(labels) - 1, 'ticks': labels},
             'y': {'label': 'Thousand transitions per second', 'min': 0, 'max': float(int(top * 1.15) + 1)}, 'series': series}
    write_json(ROOT / 'content/assets' / f'{args.asset}.json', asset)
    print(json.dumps(out, indent=1))


def effort(path, slot):
    """Mean decision time, depth-3 completion share, and abort share of one slot's seat."""
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    decisions = ms = depth_total = aborted = searches = 0
    depths = [0] * 7
    for r in rows:
        if r['game'].get('status') != 'completed':
            continue
        seat = r['game']['seats'][r['slots'].index(slot)]
        decisions += seat['decisions']
        ms += seat['decision_ms']
        depth_total += seat['effort']['depth_total']
        aborted += seat['effort']['aborted']
        searches += seat['effort'].get('searches', 0)
        for i, n in enumerate(seat['effort'].get('depths', [])):
            depths[i] += n
    n = searches or decisions
    return {'decisions': decisions, 'searches': searches, 'mean_ms': ms / decisions if decisions else None,
            'mean_depth': depth_total / n if n else None, 'aborted_share': aborted / n if n else None,
            'depth3_share': sum(depths[3:]) / n if n else None, 'depth4_share': sum(depths[4:]) / n if n else None,
            'depths': depths}


def seed_terms(half_a, half_b):
    """Per-seed effect and seating term of one swapped pair."""
    a, ra = per_seed(half_a)
    b, rb = per_seed(half_b)
    if set(a) != set(b):
        raise SystemExit('the halves must play the same seeds')
    effects, seating = [], []
    for s in sorted(a):
        d_a, d_b = a[s] / ra[s], b[s] / rb[s]
        effects.append((d_a - d_b) / 2)
        seating.append((d_a + d_b) / 2)
    return effects, seating


def pair(half_a, half_b):
    effects, seating = seed_terms(half_a, half_b)
    effect, effect_ci = interval(effects)
    seat, seat_ci = interval(seating)
    return {'seeds': len(effects), 'effect': effect, 'interval': effect_ci, 'seating': seat, 'seating_interval': seat_ci}


def wins(path, slot):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    done = [r for r in rows if r['game'].get('status') == 'completed']
    return sum(r['winner_slot'] == slot for r in done), len(done)


def games(ref):
    return Path(ref) if str(ref).endswith('.jsonl') else ROOT / 'runs' / ref / 'games.jsonl'


def pairs(args):
    arms = json.load(open(args.pairs))
    table = []
    for arm in arms:
        ga, gb = games(arm['half_a']), games(arm['half_b'])
        if not ga.exists() or not gb.exists():
            continue
        p = pair(ga, gb)
        cand = [effort(ga, 0), effort(gb, 1)]
        ctrl = [effort(ga, 1), effort(gb, 0)]
        def merge(parts):
            n = sum(x['decisions'] for x in parts)
            m = sum(x['searches'] or x['decisions'] for x in parts)
            depths = [sum(x['depths'][i] for x in parts) for i in range(7)]
            return {'decisions': n, 'searches': m,
                    'mean_ms': sum(x['mean_ms'] * x['decisions'] for x in parts) / n,
                    'mean_depth': sum(x['mean_depth'] * (x['searches'] or x['decisions']) for x in parts) / m,
                    'aborted_share': sum(x['aborted_share'] * (x['searches'] or x['decisions']) for x in parts) / m,
                    'depth3_share': sum(depths[3:]) / m, 'depth4_share': sum(depths[4:]) / m, 'depths': depths}
        wa, na = wins(ga, 0)
        wb, nb = wins(gb, 1)
        ca, _ = wins(ga, 1)
        cb, _ = wins(gb, 0)
        table.append({**arm, **p, 'candidate': merge(cand), 'control': merge(ctrl),
                      'candidate_wins': wa + wb, 'control_wins': ca + cb, 'games': na + nb})
    for row in table:
        c, k = row['candidate'], row['control']
        print(f"{row['label']:28} {row['stage']:14} effect {row['effect']:+.3f} ({row['interval'][0]:+.3f} to {row['interval'][1]:+.3f}) "
              f"seating {row['seating']:+.3f}  wins {row['candidate_wins']}-{row['control_wins']}/{row['games']}  "
              f"depth {c['mean_depth']:.2f} vs {k['mean_depth']:.2f}  depth3 {c['depth3_share']:.1%} vs {k['depth3_share']:.1%}  "
              f"aborted {c['aborted_share']:.1%} vs {k['aborted_share']:.1%}  "
              f"ms {c['mean_ms']:.0f} vs {k['mean_ms']:.0f}")
    if args.pool:
        # After-the-fact pooling: the per-seed effects of every stage of an arm, on disjoint seeds, in one interval.
        for label in dict.fromkeys(r['label'] for r in table):
            rows = [r for r in table if r['label'] == label]
            if len(rows) < 2:
                continue
            effects, seating = [], []
            for r in rows:
                e, st = seed_terms(games(r['half_a']), games(r['half_b']))
                effects += e
                seating += st
            effect, ci = interval(effects)
            seat, _ = interval(seating)
            wins_c = sum(r['candidate_wins'] for r in rows)
            wins_k = sum(r['control_wins'] for r in rows)
            n = sum(r['games'] for r in rows)
            print(f"{label:28} {'pooled':14} effect {effect:+.3f} ({ci[0]:+.3f} to {ci[1]:+.3f}) seating {seat:+.3f}  "
                  f"wins {wins_c}-{wins_k}/{n}  seeds {len(effects)}  stages {', '.join(r['stage'] for r in rows)}")
            table.append({'label': label, 'stage': 'pooled', 'seeds': len(effects), 'effect': effect, 'interval': ci,
                          'seating': seat, 'candidate_wins': wins_c, 'control_wins': wins_k, 'games': n,
                          'stages': [r['stage'] for r in rows]})
    if args.out:
        write_json(Path(args.out), table)
    table_plot = [r for r in table if r['stage'] != 'pooled']
    if args.asset and table_plot:
        table = table_plot
        stages = list(dict.fromkeys(r['stage'] for r in table))
        labels = list(dict.fromkeys(r['label'] for r in table))
        series = []
        for stage in stages:
            points = [{'x': labels.index(r['label']), 'y': round(r['effect'], 4), 'low': round(r['interval'][0], 4), 'high': round(r['interval'][1], 4)}
                      for r in table if r['stage'] == stage]
            series.append({'label': stage, 'points': points})
        lo = min(p['low'] for s in series for p in s['points']) - 0.03
        hi = max(p['high'] for s in series for p in s['points']) + 0.03
        asset = {'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'title': 'Equal-budget arms against the depth-3 control',
                 'evidence': 'measured', 'source': args.source, 'caption': args.caption,
                 'x': {'label': 'Arm', 'min': 0, 'max': len(labels) - 1, 'ticks': labels},
                 'y': {'label': 'Wins per game, candidate minus control', 'min': round(min(lo, -0.05), 2), 'max': round(max(hi, 0.05), 2)},
                 'series': series, 'reference': {'y': 0, 'label': 'no difference'}}
        write_json(ROOT / 'content/assets' / f'{args.asset}.json', asset)


def budget(args):
    data = json.loads(Path(args.budget).read_text())
    labels = list(dict.fromkeys(r['label'] for r in data['results']))
    for label in labels:
        rows = [r for r in data['results'] if r['label'] == label]
        ms = [r['wallMs'] for r in rows]
        cpu = [r['cpuMs'] for r in rows]
        depths = [r['depthCompleted'] for r in rows]
        print(f"{label:24} n={len(rows)} wall median {statistics.median(ms):.0f} ms p90 {quantile(ms, .9):.0f} ms "
              f"(cpu median {statistics.median(cpu):.0f} p90 {quantile(cpu, .9):.0f})  depth mean {statistics.mean(depths):.2f}  "
              f"depth3+ {sum(d >= 3 for d in depths) / len(depths):.0%}  depth4 {sum(d >= 4 for d in depths) / len(depths):.0%}  "
              f"aborted {sum(r['aborted'] for r in rows) / len(rows):.0%}  transitions median {statistics.median(r['transitions'] for r in rows):.0f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('rate')
    r.add_argument('rate')
    r.add_argument('--asset', default='search-rate-wasm')
    r.add_argument('--source', required=True)
    r.add_argument('--caption', required=True)
    p = sub.add_parser('pairs')
    p.add_argument('pairs')
    p.add_argument('--asset')
    p.add_argument('--out')
    p.add_argument('--pool', action='store_true', help='also print the after-the-fact pooled estimate of every arm over its stages')
    p.add_argument('--source', default='')
    p.add_argument('--caption', default='')
    b = sub.add_parser('budget')
    b.add_argument('budget')
    args = parser.parse_args()
    {'rate': rate, 'pairs': pairs, 'budget': budget}[args.command](args)


if __name__ == '__main__':
    main()
