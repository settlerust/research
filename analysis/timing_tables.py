"""Seating-corrected effects and development-card diagnostics for development/timing-tables.

Every cohort of the study is a paired engine-arena tournament on deterministic boards, each
board played once per rotation of the four slots. Each arm is measured as a swapped pair:
half A seats the candidate in slot 0 and the control in slot 1, half B swaps them. The
seating-corrected effect is the per-seed half-difference of the two slot-0-minus-slot-1
contrasts and the seating term their half-sum (analysis/seating_pair.py). This script
discovers the study's experiments from experiments/*.toml, pairs halves by arm, lineup, and
seeds, prints every contrast and the per-arm diagnostics (development cards bought, knights
played, army awards, cities built, first city turn, points, decision time), and writes the
report's plot asset. Run it from the research checkout: `python3 analysis/timing_tables.py`.
"""
import json
import math
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

STUDY = 'development/timing-tables'
ARMS = ['buy_tempo', 'hold_knight', 'knight_play_value']
BUILD_KEYS = ['development_bought', 'knights_played', 'army_awards', 'cities_built',
              'roads_built', 'player_trades', 'cards_discarded']


def blend_of(seat):
    """The hand-written blend strength of a seat spec: 0 for the tables alone."""
    if ':' not in seat:
        return 0.0
    leaf = json.loads(seat.split(':', 1)[1]).get('leaf') or {}
    return leaf.get('hand', 0.0)


def study_experiments():
    out = []
    for file in sorted((ROOT / 'experiments').glob('*.toml')):
        data = tomllib.loads(file.read_text())
        if data.get('study') != STUDY:
            continue
        seats = data['players']
        arm = next((a for a in ARMS if f'"{a}":true' in seats[0] or f'"{a}":true' in seats[1]), None)
        if arm is None:
            continue
        cand = 0 if f'"{arm}":true' in seats[0] else 1
        lineup = 'L1' if seats[2] == 'eta' else 'L2'
        blend = blend_of(seats[1 - cand])
        out.append({'id': data['id'], 'arm': arm, 'half': 'A' if cand == 0 else 'B',
                    'lineup': lineup, 'seeds': data['seeds'], 'blend': blend, 'seats': seats})
    return out


def latest_run(experiment):
    runs = []
    for manifest in (ROOT / 'runs').glob('*/manifest.json'):
        data = json.loads(manifest.read_text())
        if data.get('experiment') == experiment and (manifest.parent / 'summary.json').exists():
            summary = json.loads((manifest.parent / 'summary.json').read_text())
            if summary.get('status') == 'completed':
                runs.append((data['created_at'], manifest.parent.name, summary))
    return sorted(runs)[-1] if runs else None


def games(run_id):
    rows = (ROOT / 'runs' / run_id / 'games.jsonl').read_text().splitlines()
    return [json.loads(line) for line in rows
            if line.strip() and json.loads(line)['game']['status'] == 'completed']


def per_seed(rows, a, b):
    """Slot `a` wins minus slot `b` wins per seed, averaged over that seed's rotations."""
    by = {}
    for r in rows:
        by.setdefault(r['seed'], []).append((r['winner_slot'] == a) - (r['winner_slot'] == b))
    return {seed: sum(v) / len(v) for seed, v in by.items()}


def interval(values):
    xs = list(values)
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / max(1, len(xs) - 1))
    se = sd / math.sqrt(len(xs))
    return {'mean': mean, 'se': se, 'low': mean - 1.96 * se, 'high': mean + 1.96 * se,
            'seeds': len(xs)}


def combine(rows_a, rows_b):
    """Seating-corrected effect and seating term of a swapped pair, matching
    analysis/seating_pair.py: per seed, half the difference of the two halves'
    slot-0-minus-slot-1 contrasts (effect) and half their sum (seating term),
    each with a normal-approximation 95 percent interval over seeds."""
    da = per_seed(rows_a, 0, 1)
    db = per_seed(rows_b, 0, 1)
    if set(da) != set(db):
        raise SystemExit('the halves must play the same seeds')
    seeds = sorted(da)
    effect = interval([(da[s] - db[s]) / 2 for s in seeds])
    seating = interval([(da[s] + db[s]) / 2 for s in seeds])
    return effect, seating


def pooled(effects):
    """Inverse-variance pooling of per-stage effects; an after-the-fact pooling."""
    weights = [1.0 / e['se'] ** 2 for e in effects]
    mean = sum(e['mean'] * w for e, w in zip(effects, weights)) / sum(weights)
    se = math.sqrt(1.0 / sum(weights))
    return {'mean': mean, 'se': se, 'low': mean - 1.96 * se, 'high': mean + 1.96 * se,
            'seeds': sum(e['seeds'] for e in effects)}


def seat_means(rows, slot):
    """Per-game means for one slot over completed games."""
    recs = []
    for r in rows:
        i = r['slots'].index(slot)
        recs.append((r['game']['seats'][i], r))
    out = {}
    for key in BUILD_KEYS:
        out[key] = sum(s.get(key, 0) for s, _ in recs) / len(recs)
    first = [s['first_city_turn'] for s, _ in recs if s.get('first_city_turn') is not None]
    out['first_city_turn'] = sum(first) / len(first) if first else None
    out['first_city_games'] = len(first)
    out['points'] = sum(s['points'] for s, _ in recs) / len(recs)
    decisions = sum(s['decisions'] for s, _ in recs)
    out['decision_ms'] = sum(s['decision_ms'] for s, _ in recs) / decisions if decisions else None
    out['wins'] = sum(1 for _, r in recs if r['winner_slot'] == slot)
    return out


def fmt(c, digits=3):
    return f"{c['mean']:+.3f} ({c['low']:+.3f} to {c['high']:+.3f})"


# Registered on the full blend (leaf.hand 1.0) and withdrawn before running: the blend
# screen measured hand 1.0 at -0.207 wins per game against the tables alone, so leaf-term
# arms are measured on the quarter blend instead. These experiments were never run.
WITHDRAWN = {'00d8c63d-5ed9-47ef-aacf-c8efdfae7288', 'e5715fe9-b44b-4273-a3b0-64ae25ca1b7e',
             'e4ddbc81-32bb-4a70-b17f-38958ae86a9d', '2d22c801-4004-4baa-9551-1c2defee2a0b'}


def main():
    experiments = [e for e in study_experiments() if e['id'] not in WITHDRAWN]
    pairs = {}
    for e in experiments:
        pairs.setdefault((e['arm'], e['lineup'], e['seeds'], e['blend']), {})[e['half']] = e
    results = {}
    for (arm, lineup, seeds, blend), halves in sorted(pairs.items()):
        label = f'{arm} | {lineup} | seeds {seeds} | hand {blend:g}'
        if set(halves) != {'A', 'B'}:
            print(f'INCOMPLETE PAIR {label}: halves {sorted(halves)}')
            continue
        rows = {}
        for half, e in halves.items():
            run = latest_run(e['id'])
            if not run:
                print(f'NO COMPLETED RUN {label} half {half} ({e["id"]})')
                rows[half] = None
                continue
            _, run_id, summary = run
            rows[half] = {'run': run_id, 'summary': summary, 'games': games(run_id),
                          'experiment': e['id']}
        if not all(rows.values()):
            continue
        a, b = rows['A'], rows['B']
        ca = interval(per_seed(a['games'], 0, 1).values())
        cb = interval(per_seed(b['games'], 0, 1).values())
        effect, seating = combine(a['games'], b['games'])
        # Candidate minus control diagnostics across both seatings.
        cand = seat_means(a['games'], 0)
        cand_b = seat_means(b['games'], 1)
        ctrl = seat_means(a['games'], 1)
        ctrl_b = seat_means(b['games'], 0)
        merged_cand = {k: (cand[k] + cand_b[k]) / 2 if cand[k] is not None else None
                       for k in cand}
        merged_ctrl = {k: (ctrl[k] + ctrl_b[k]) / 2 if ctrl[k] is not None else None
                       for k in ctrl}
        key = (arm, lineup, seeds, blend)
        results[key] = {'effect': effect, 'seating': seating, 'ca': ca, 'cb': cb,
                        'runs': {'A': a['run'], 'B': b['run']},
                        'experiments': {'A': a['experiment'], 'B': b['experiment']},
                        'candidate': merged_cand, 'control': merged_ctrl,
                        'wins': {'A': [cand['wins'], ctrl['wins']],
                                 'B': [ctrl_b['wins'], cand_b['wins']]}}
        print(label)
        print(f"  half A (candidate slot 0, run {a['run'][:8]}): {fmt(ca)} "
              f"[{cand['wins']} vs {ctrl['wins']} of 256]")
        print(f"  half B (candidate slot 1, run {b['run'][:8]}): {fmt(cb)} "
              f"[control {ctrl_b['wins']} vs candidate {cand_b['wins']} of 256]")
        print(f"  seating-corrected effect: {fmt(effect)}; seating term {fmt(seating)}")
        print(f"  cards bought {merged_cand['development_bought']:.2f} vs "
              f"{merged_ctrl['development_bought']:.2f}; knights {merged_cand['knights_played']:.2f} vs "
              f"{merged_ctrl['knights_played']:.2f}; army {merged_cand['army_awards']:.2f} vs "
              f"{merged_ctrl['army_awards']:.2f}; cities {merged_cand['cities_built']:.2f} vs "
              f"{merged_ctrl['cities_built']:.2f}; decision ms {merged_cand['decision_ms']:.1f} vs "
              f"{merged_ctrl['decision_ms']:.1f}")
    # After-the-fact pooling per arm and blend: L1 stages together, then all stages.
    print('\nPooled (after the fact):')
    arm_blends = sorted({(a, b) for (a, _, _, b) in results})
    for arm, blend in arm_blends:
        l1 = [r for (a, lineup, _, b), r in results.items()
              if a == arm and b == blend and lineup == 'L1']
        all_ = [r for (a, _, _, b), r in results.items() if a == arm and b == blend]
        for stage_label, group in [('L1', l1), ('all stages', all_)]:
            if len(group) > 1:
                p = pooled([g['effect'] for g in group])
                print(f"  {arm} (hand {blend:g}) pooled {stage_label}: {fmt(p)} "
                      f"over {p['seeds']} seeds")
    write_json(ROOT / 'analysis/timing_tables.json', {
        f'{arm}|{lineup}|{seeds}|hand {blend:g}': {
            'effect': r['effect'], 'seating': r['seating'], 'half_A': r['ca'], 'half_B': r['cb'],
            'runs': r['runs'], 'experiments': r['experiments'],
            'candidate': r['candidate'], 'control': r['control'], 'wins': r['wins']}
        for (arm, lineup, seeds, blend), r in results.items()})
    print('wrote analysis/timing_tables.json')

    # The report's plot: one point per swapped pair, in arm then stage order.
    stage_label = {('L1', '0-63'): 'development, boards 0-63',
                   ('L1', '800-863'): 'confirmation, boards 800-863',
                   ('L2', '800-863'): 'population, boards 800-863'}
    order = [('buy_tempo', 0.0, 'buy tempo'), ('hold_knight', 0.0, 'hold knight'),
             ('knight_play_value', 0.25, 'knight value (quarter blend)'),
             ('knight_play_value', 1.0, 'knight value (full blend)')]
    stage_order = {'0-63': 0, '800-863': 1}
    ticks, points = [], []
    for arm, blend, arm_name in order:
        entries = [(lineup, seeds, r) for (a, lineup, seeds, b), r in results.items()
                   if a == arm and b == blend]
        for lineup, seeds, r in sorted(entries, key=lambda t: (stage_order.get(t[1], 9), t[0])):
            ticks.append(f"{arm_name}, {stage_label.get((lineup, seeds), lineup + ' ' + seeds)}")
            e = r['effect']
            points.append({'x': len(ticks) - 1, 'y': round(e['mean'], 4),
                           'low': round(e['low'], 4), 'high': round(e['high'], 4)})
    if points:
        lo = min(p['low'] for p in points) - 0.03
        hi = max(p['high'] for p in points) + 0.03
        runs_note = ('; '.join(f"{r['runs']['A'][:8]}, {r['runs']['B'][:8]}"
                               for r in results.values()))
        data = {'schema': 1, 'kind': 'plot', 'variant': 'scatter',
                'title': 'Development-card timing switches under the learned tables leaf',
                'evidence': 'measured',
                'source': ('Engine-arena swapped pairs of 512 games each on deterministic boards played '
                           'once per rotation, the candidate and the control in slots 0 and 1 in both '
                           'seatings; the builders lineup (L1) seats an ETA and a fast builder beside the '
                           'searches, the population lineup (L2) a third tables search and an ETA. '
                           'Each point is the per-seed half-difference of the two slot-0-minus-slot-1 '
                           'contrasts of a pair with its 95% interval over 64 boards. Runs: '
                           + runs_note + '.'),
                'caption': ('Each point is one swapped pair\u2019s seating-corrected effect in wins per '
                            'game with its 95% interval over boards; the two candidate-rule arms play '
                            'under the tables alone, the knight-value arm under the named blend.'),
                'x': {'label': 'Cohort', 'min': 0, 'max': len(ticks) - 1, 'ticks': ticks},
                'y': {'label': 'Seating-corrected effect, wins per game',
                      'min': round(lo, 2), 'max': round(hi, 2)},
                'series': [{'label': 'Seating-corrected effect (swapped pair)', 'points': points}]}
        write_json(ROOT / 'content/assets/timing-tables-effects.json', data)
        print('wrote content/assets/timing-tables-effects.json')


if __name__ == '__main__':
    main()
