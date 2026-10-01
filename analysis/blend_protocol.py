"""Seating-corrected effect of a swapped pair of protocol-arena cohorts. Half A seats the
candidate in slot 0 and the control in slot 1, half B swaps them, both on the same
deterministic seeds through the authoritative server. The effect of the candidate is the
per-seed half-difference of the two slot-0-minus-slot-1 win contrasts and the seating term
their half-sum, each with a normal-approximation 95 percent interval over seeds.

The script reads the harness's per-game records (`runs/RUN/match-*/result.json`), the run
summaries, and the public event tapes; when the remote seats ran with
`SETTLERS_SEARCH_TRACE` set, it also summarizes the per-decision traces kept in the
private policy logs (search time, wall time, completed depth) per policy. Only aggregates
are printed; nothing private leaves the run directory.

    python3 analysis/blend_protocol.py RUN_A RUN_B [--assets content/assets --slug blend-protocol]
"""
import argparse
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def load_run(run_id):
    folder = ROOT / 'runs' / run_id
    manifest = json.loads((folder / 'manifest.json').read_text())
    summary = json.loads((folder / 'summary.json').read_text())
    matches = [json.loads((m / 'result.json').read_text()) for m in sorted(folder.glob('match-*'))]
    return {'id': run_id, 'folder': folder, 'manifest': manifest, 'summary': summary, 'matches': matches}


def validity(run):
    completed = [m for m in run['matches'] if m['status'] == 'completed']
    timeouts = sum(m['event_counts'].get('timed_out', 0) for m in run['matches'])
    return {'planned': run['manifest']['games'], 'attempted': len(run['matches']), 'completed': len(completed),
            'other': sorted({m['status'] for m in run['matches'] if m['status'] != 'completed'}),
            'timeout_moves': timeouts, 'status': run['summary'].get('status')}


def per_seed(run):
    """Per-seed slot-0-minus-slot-1 win difference in wins per game over the seed's rotations."""
    by_seed = {}
    for m in run['matches']:
        if m['status'] != 'completed':
            continue
        by_seed.setdefault(m['seed'], []).append((m['winner'] == m['slots'].index(0)) - (m['winner'] == m['slots'].index(1)))
    return {seed: sum(d) / len(d) for seed, d in by_seed.items()}


def interval(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, [mean - 1.96 * se, mean + 1.96 * se]


def fmt(mean, bounds):
    return f'{mean:+.3f} ({bounds[0]:+.3f} to {bounds[1]:+.3f})'


def wilson_table(run):
    lines = ['| Slot / policy | Wins | Completed | Win rate | 95% Wilson interval | Mean points |',
             '| --- | ---: | ---: | ---: | --- | ---: |']
    for row in run['summary']['players']:
        low, high = row['wilson95']
        lines.append(f"| {row['slot']} / `{row['policy']}` | {row['wins']} | {row['completed']} | "
                     f"{row['win_rate']:.1%} | {low:.1%} to {high:.1%} | {row['mean_points']:.2f} |")
    return '\n'.join(lines)


def play_statistics(run):
    """Per-policy per-game counts from the public event tapes, and own-turn wall time from
    the public batch timestamps (a turn spans every decision and every opponent reply)."""
    players = run['manifest']['players']
    totals = {p: {'games': 0, 'cities': 0, 'settlements': 0, 'roads': 0, 'development': 0,
                  'player_trades': 0, 'bank_trades': 0, 'discards': 0, 'points': 0, 'turns': 0, 'turn_ms': 0.}
              for p in players}
    for m in run['matches']:
        if m['status'] != 'completed':
            continue
        policy_of_seat = {seat: players[slot] for seat, slot in enumerate(m['slots'])}
        for seat, policy in policy_of_seat.items():
            totals[policy]['games'] += 1
            totals[policy]['points'] += m['points'][seat]
        changes = []
        for line in (run['folder'] / f"match-{m['index']:04d}" / 'events.jsonl').read_text().splitlines():
            batch = json.loads(line)
            for e in batch['events']:
                if e['type'] != 'rule':
                    continue
                r = e['event']
                kind = r['type']
                if kind == 'turn_changed':
                    changes.append((batch['timestamp_ms'], r['player']))
                    continue
                if 'player' not in r:
                    continue
                t = totals[policy_of_seat[r['player']]]
                if kind == 'built_city':
                    t['cities'] += 1
                elif kind == 'built_settlement':
                    t['settlements'] += 1
                elif kind == 'built_road':
                    t['roads'] += 1
                elif kind == 'bought_development':
                    t['development'] += 1
                elif kind == 'traded':
                    t['player_trades'] += 1
                    totals[policy_of_seat[r['other']]]['player_trades'] += 1
                elif kind == 'bank_traded':
                    t['bank_trades'] += 1
                elif kind == 'discarded':
                    t['discards'] += 1
        for (start, seat), (end, _) in zip(changes, changes[1:]):
            t = totals[policy_of_seat[seat]]
            t['turns'] += 1
            t['turn_ms'] += end - start
    rows = {}
    for policy, t in totals.items():
        g = max(1, t['games'])
        rows[policy] = {k: t[k] / g for k in ('cities', 'settlements', 'roads', 'development', 'player_trades',
                                              'bank_trades', 'discards', 'points')}
        rows[policy]['turn_seconds'] = t['turn_ms'] / max(1, t['turns']) / 1000
        rows[policy]['games'] = t['games']
    return rows


def play_table(runs):
    lines = ['| Half | Policy | Cities | Settlements | Roads | Development cards | Player trades | Bank trades | Discards | Mean points | Own turn (s) |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for label, run in runs:
        for policy, r in play_statistics(run).items():
            lines.append(f"| {label} | `{policy}` | {r['cities']:.2f} | {r['settlements']:.2f} | {r['roads']:.2f} | "
                         f"{r['development']:.2f} | {r['player_trades']:.2f} | {r['bank_trades']:.2f} | {r['discards']:.2f} | "
                         f"{r['points']:.2f} | {r['turn_seconds']:.2f} |")
    return '\n'.join(lines)


def traces(run):
    """Per-policy decision traces from the private policy logs, when the seats wrote them."""
    players = run['manifest']['players']
    out = {p: [] for p in players}
    for m in run['matches']:
        if m['status'] != 'completed':
            continue
        private = run['folder'] / f"match-{m['index']:04d}" / 'private'
        for seat, slot in enumerate(m['slots']):
            log = private / f'policy-{seat}.log'
            if not log.exists():
                continue
            for line in log.read_text(errors='replace').splitlines():
                if '"trace":"search"' not in line:
                    continue
                try:
                    out[players[slot]].append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return {p: rows for p, rows in out.items() if rows}


def fallbacks(run):
    """Search fallbacks per policy: decisions where the seat's search returned an error and the
    runner played the first legal action, counted from the private policy logs."""
    players = run['manifest']['players']
    counts = {p: 0 for p in players}
    for m in run['matches']:
        private = run['folder'] / f"match-{m['index']:04d}" / 'private'
        for seat, slot in enumerate(m['slots']):
            log = private / f'policy-{seat}.log'
            if log.exists():
                counts[players[slot]] += sum('expectimax fallback' in line for line in log.read_text(errors='replace').splitlines())
    return counts


def quantile(values, q):
    values = sorted(values)
    position = (len(values) - 1) * q
    low = math.floor(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def trace_rows(run):
    """Per-policy aggregates. Contested decisions have at least two root actions; a single
    candidate never deepens past the first depth, so depth shares are reported over contested
    main-phase decisions."""
    rows = {}
    for policy, decisions in traces(run).items():
        contested = [d for d in decisions if d['phase'] == 'main' and d['root_actions'] >= 2]
        rows[policy] = {
            'decisions': len(decisions), 'contested': len(contested),
            'mean_ms': statistics.fmean(d['wall_ms'] for d in decisions),
            'median_ms': quantile([d['wall_ms'] for d in decisions], .5),
            'p90_ms': quantile([d['wall_ms'] for d in decisions], .9),
            'contested_mean_ms': statistics.fmean(d['wall_ms'] for d in contested) if contested else float('nan'),
            'contested_median_ms': quantile([d['wall_ms'] for d in contested], .5) if contested else float('nan'),
            'depth3': sum(d['depth_completed'] >= 3 for d in contested) / len(contested) if contested else float('nan'),
            'depth2': sum(d['depth_completed'] == 2 for d in contested) / len(contested) if contested else float('nan'),
            'depth1': sum(d['depth_completed'] <= 1 for d in contested) / len(contested) if contested else float('nan'),
            'aborted': sum(bool(d['aborted']) for d in contested) / len(contested) if contested else float('nan'),
            'at_budget': sum(d['wall_ms'] >= 1500 for d in contested) / len(contested) if contested else float('nan'),
            'max_ms': max(d['wall_ms'] for d in decisions),
            'policy_field': sorted({d['policy'] for d in decisions}),
        }
    return rows


def trace_table(runs):
    lines = ['| Half | Policy | Decisions | Contested | Mean ms | Median ms | 90th pct ms | Contested mean ms | Contested median ms | Depth 3 | Depth 2 | Depth 1 | Aborted | At budget | Max ms | Evaluator |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    any_rows = False
    for label, run in runs:
        for policy, r in trace_rows(run).items():
            any_rows = True
            lines.append(f"| {label} | `{policy}` | {r['decisions']} | {r['contested']} | {r['mean_ms']:.0f} | {r['median_ms']:.0f} | {r['p90_ms']:.0f} | "
                         f"{r['contested_mean_ms']:.0f} | {r['contested_median_ms']:.0f} | {r['depth3']:.1%} | {r['depth2']:.1%} | {r['depth1']:.1%} | "
                         f"{r['aborted']:.1%} | {r['at_budget']:.1%} | {r['max_ms']:.0f} | {', '.join(r['policy_field'])} |")
    return '\n'.join(lines) if any_rows else 'No search traces in the private policy logs.'


def chart_asset(run, title, caption):
    rows = [{'label': f"{r['policy']} · slot {r['slot']}", 'value': r['win_rate'], 'low': r['wilson95'][0],
             'high': r['wilson95'][1], 'n': r['completed']} for r in run['summary']['players'] if r['wilson95']]
    return {'schema': 1, 'kind': 'chart', 'title': title, 'unit': 'fraction', 'caption': caption, 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('half_a', help='run UUID with the candidate in slot 0')
    parser.add_argument('half_b', help='run UUID with the candidate in slot 1')
    parser.add_argument('--candidate', default='ntuple-leaf-blend')
    parser.add_argument('--control', default='ntuple-leaf')
    parser.add_argument('--assets', help='write chart and plot assets into this directory')
    parser.add_argument('--slug', default='blend-protocol')
    args = parser.parse_args()
    a, b = load_run(args.half_a), load_run(args.half_b)
    for label, run, slot0, slot1 in (('A', a, args.candidate, args.control), ('B', b, args.control, args.candidate)):
        players = run['manifest']['players']
        if players[0] != slot0 or players[1] != slot1:
            raise SystemExit(f'half {label} lineup is {players}, expected {slot0} in slot 0 and {slot1} in slot 1')
    va, vb = validity(a), validity(b)
    print(f"Half A: {va}\nHalf B: {vb}")
    da, db = per_seed(a), per_seed(b)
    if set(da) != set(db):
        raise SystemExit('the halves must play the same seeds')
    seeds = sorted(da)
    contrast_a, ci_a = interval([da[s] for s in seeds])
    contrast_b, ci_b = interval([db[s] for s in seeds])
    effect, ci_e = interval([(da[s] - db[s]) / 2 for s in seeds])
    seating, ci_s = interval([(da[s] + db[s]) / 2 for s in seeds])
    print(f"seeds: {len(seeds)} ({seeds[0]}-{seeds[-1]})")
    print(f"half A slot 0 minus slot 1 (candidate minus control): {fmt(contrast_a, ci_a)}")
    print(f"half B slot 0 minus slot 1 (control minus candidate): {fmt(contrast_b, ci_b)}")
    print(f"seating-corrected effect of {args.candidate} over {args.control}: {fmt(effect, ci_e)}")
    print(f"seating term: {fmt(seating, ci_s)}")
    wins = lambda run, policy: next(r['wins'] for r in run['summary']['players'] if r['policy'] == policy)
    print(f"candidate wins A/B: {wins(a, args.candidate)}/{wins(b, args.candidate)}; control wins A/B: {wins(a, args.control)}/{wins(b, args.control)}")
    print(f"mean turns A/B: {a['summary']['mean_turns']:.1f}/{b['summary']['mean_turns']:.1f}")
    print('\n## Half A\n\n' + wilson_table(a) + '\n\n## Half B\n\n' + wilson_table(b))
    print('\n## Play statistics per seat per game (public tapes)\n\n' + play_table([('A', a), ('B', b)]))
    print('\n## Decision traces (private policy logs, aggregates only)\n\n' + trace_table([('A', a), ('B', b)]))
    print(f"\nsearch fallbacks per policy: A {fallbacks(a)}; B {fallbacks(b)}")
    print('\n## Per-seed contrasts\n\n| Seed | Half A | Half B | Effect | Seating |\n| --- | ---: | ---: | ---: | ---: |')
    for s in seeds:
        print(f'| {s} | {da[s]:+.2f} | {db[s]:+.2f} | {(da[s] - db[s]) / 2:+.3f} | {(da[s] + db[s]) / 2:+.3f} |')
    if args.assets:
        folder = Path(args.assets)
        folder.mkdir(parents=True, exist_ok=True)
        # Half A's chart and replay come from `just publish RUN_A --slug SLUG`; only half B's chart is written here.
        asset = chart_asset(b, 'Win rate by competitor, half B',
                            f"Run {b['id']}. {b['summary']['completed']} completed of {b['manifest']['games']} planned games. 95% Wilson intervals; descriptive evidence only.")
        (folder / f'{args.slug}-half-b-wins.json').write_text(json.dumps(asset, indent=2) + '\n')
        span = max(abs(v) for v in (*ci_a, *ci_b, *ci_e, *ci_s)) + 0.05
        plot = {
            'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'evidence': 'measured',
            'title': 'The quarter blend against ntuple-leaf through the protocol arena',
            'source': f"Source: analysis/blend_protocol.py over runs {a['id']} (half A) and {b['id']} (half B); seeds {seeds[0]} to {seeds[-1]}, four rotations per seed per half, {va['completed']} and {vb['completed']} completed games. Contrasts are candidate minus control in wins per game; the effect is half the per-seed difference of the two halves' slot-0-minus-slot-1 contrasts and the seating term half their sum; 95% normal intervals over seeds.",
            'caption': 'Each seating alone carries the turn-order term; the corrected effect is the middle point.',
            'x': {'label': 'Contrast', 'min': 0, 'max': 3, 'ticks': ['Half A (blend first)', 'Half B (blend second)', 'Seating-corrected effect', 'Seating term']},
            'y': {'label': 'Wins per game', 'min': -round(span, 2), 'max': round(span, 2)},
            'series': [{'label': f'{len(seeds)} seeds, both seatings', 'points': [
                {'x': 0, 'y': round(contrast_a, 3), 'low': round(ci_a[0], 3), 'high': round(ci_a[1], 3)},
                {'x': 1, 'y': round(-contrast_b, 3), 'low': round(-ci_b[1], 3), 'high': round(-ci_b[0], 3)},
                {'x': 2, 'y': round(effect, 3), 'low': round(ci_e[0], 3), 'high': round(ci_e[1], 3)},
                {'x': 3, 'y': round(seating, 3), 'low': round(ci_s[0], 3), 'high': round(ci_s[1], 3)}]}],
            'reference': {'y': 0, 'label': 'No difference'},
        }
        (folder / f'{args.slug}-effects.json').write_text(json.dumps(plot, indent=2) + '\n')
        print(f'\nassets written to {folder}')


if __name__ == '__main__':
    main()
