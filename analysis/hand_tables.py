"""Seating-corrected effects and diagnostics for the hand-tables study (risk/hand-tables).

Every cohort is a paired deterministic engine-arena tournament, 64 seeds played once per
rotation of the four slots (256 games). Each arm is a swapped pair on the same seeds: half A
seats the candidate in slot 0 and the control in slot 1, half B swaps them. The effect is the
per-seed half-difference of the two slot-0-minus-slot-1 contrasts and the seating term their
half-sum, each with a normal-approximation 95 percent interval over seeds (the same arithmetic
as analysis/seating_pair.py).

Arms: spend_down and discard_projection sit on the learned n-tuple tables leaf alone; the
hand_risk arm removes the seven-risk term (weights.hand_risk 0 against the default 1) on top
of the blended leaf (tables plus the hand-written terms at hand 1.0 in both seats), because
the term is inert under the tables alone. Stages: 1 development (builders lineup, seeds
0-63), 2 confirmation (builders, fresh seeds 800-863), 3 population (a third search in slot 2
and eta in slot 3, seeds 800-863). Stage 4 (extension, seeds 864-927, both lineups) is added
only when the pooled L1 effect over 128 seeds is positive and its interval comes within 0.03
of zero.

Run from the research checkout: `python3 analysis/hand_tables.py`. Every value is recomputed
from the retained run folders under runs/; the script picks each experiment's latest completed
run. With `--asset` it also writes the report plot to content/assets/hand-tables-effects.json.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ARMS = ['spend_down', 'discard_projection', 'hand_risk']
ARM_TITLES = {
    'spend_down': 'spend_down',
    'discard_projection': 'discard_projection',
    'hand_risk': 'hand_risk 0 (on the blend)',
}
STAGES = ['stage1', 'stage2', 'stage3', 'stage4l1', 'stage4l2']
STAGE_TITLES = {
    'stage1': 'development, builders, seeds 0-63',
    'stage2': 'confirmation, builders, seeds 800-863',
    'stage3': 'population, third search at the table, seeds 800-863',
    'stage4l1': 'extension, builders, seeds 864-927',
    'stage4l2': 'extension, population, seeds 864-927',
}

# experiment id -> (stage, arm, half). Half A seats the candidate in slot 0, half B in slot 1.
COHORTS = {
    'a955b267-9ff0-40c1-82b7-4aa4edc9ff6e': ('stage1', 'spend_down', 'A'),
    'c492642c-4347-480a-b2ff-29b8f21578ab': ('stage1', 'spend_down', 'B'),
    '3937f009-a9ac-4402-941d-5e549525e838': ('stage1', 'discard_projection', 'A'),
    '30413802-3438-4da7-801a-1930b12b8933': ('stage1', 'discard_projection', 'B'),
    '8482a56b-7a41-430f-9d4f-19dcfed08e3a': ('stage1', 'hand_risk', 'A'),  # withdrawn before running: full blend superseded
    '8dfff424-e403-47c4-89ec-029b203d89e4': ('stage1', 'hand_risk', 'B'),  # withdrawn before running
    '826a6d8e-1b8a-4797-addc-f5454fa4d954': ('stage1', 'hand_risk', 'A'),  # quarter blend (hand 0.25), primary
    '525aa23e-6191-4ae8-aabf-b1082da41b2d': ('stage1', 'hand_risk', 'B'),
    '36feacf1-4e3e-4a42-95dc-c04e5c876c51': ('stage2', 'spend_down', 'A'),
    'f9d49130-b3c8-45a6-a08e-6d5bb0c61073': ('stage2', 'spend_down', 'B'),
    'cd34b338-7485-4ff9-bc83-f401c08bc6e8': ('stage2', 'discard_projection', 'A'),
    '45db85c1-1e68-4d90-a82e-29e19ae2acf8': ('stage2', 'discard_projection', 'B'),
    '9249ab83-c0b0-485a-a08e-e734b82b4cdc': ('stage2', 'hand_risk', 'A'),  # withdrawn before running: full blend superseded
    '198621cf-57ef-4e5b-a892-3989fe65650c': ('stage2', 'hand_risk', 'B'),  # withdrawn before running
    'dce23ad1-0f66-417e-8a07-56fc52e26992': ('stage2', 'hand_risk', 'A'),  # quarter blend (hand 0.25), primary
    '72f45c36-9c85-419c-b41a-de7f2d761eec': ('stage2', 'hand_risk', 'B'),
    '25cf8f50-1d9c-4327-bd46-74773339355a': ('stage3', 'spend_down', 'A'),
    'b05633ce-e0f4-472b-a07c-5aa348f292af': ('stage3', 'spend_down', 'B'),
    '107448ed-68a4-4ee9-876d-08c78ba7d576': ('stage3', 'discard_projection', 'A'),
    '5330c9c8-a119-446e-8ed6-bfdbd20d2f5b': ('stage3', 'discard_projection', 'B'),
    'd2f026f6-aaaf-4173-ac65-f39e52d27a2d': ('stage3', 'hand_risk', 'A'),  # withdrawn before running: full blend superseded
    'a1d96405-f132-45d1-825f-2117844deea7': ('stage3', 'hand_risk', 'B'),  # withdrawn before running
    '1547ca49-dffd-4e2e-bd52-41934ae1180f': ('stage3', 'hand_risk', 'A'),  # quarter blend (hand 0.25), primary
    '93304090-43f2-49e9-b30a-8cfc6bbe9d45': ('stage3', 'hand_risk', 'B'),
    '3c319637-e3da-420d-a9c8-381a469036cf': ('stage4l1', 'discard_projection', 'A'),
    '8dad3d8b-5636-41d1-8c19-bf02370cbf42': ('stage4l1', 'discard_projection', 'B'),
    '316cb7a7-5b95-42bf-ade4-f7356f9ef6e1': ('stage4l2', 'discard_projection', 'A'),
    'dcd15bb4-deb1-4726-a63b-da6e0e83120d': ('stage4l2', 'discard_projection', 'B'),
}
# The hand-1.0 hand-risk registrations (8482a56b, 8dfff424, 9249ab83, 198621cf, d2f026f6,
# a1d96405) were withdrawn before running and have no runs: a program screen on 2026-09-11
# measured the full blend at -0.207 wins per game against the tables alone, so the arm moved
# to the quarter blend. They stay in the file so their registrations remain explained.
# Extension cohorts are appended here if the pooled L1 rule triggers them.

DIAGNOSTICS = ['cards_discarded', 'turns_over_limit', 'times_robbed', 'bank_trades',
               'player_trades', 'development_bought', 'cities_built', 'roads_built']


def latest_run(experiment):
    runs = []
    for manifest in (ROOT / 'runs').glob('*/manifest.json'):
        try:
            data = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if data.get('experiment') == experiment and (manifest.parent / 'summary.json').exists():
            summary = json.loads((manifest.parent / 'summary.json').read_text())
            if summary.get('status') == 'completed':
                runs.append((data['created_at'], manifest.parent.name, summary))
    return sorted(runs)[-1] if runs else None


def games(run_id):
    rows = (ROOT / 'runs' / run_id / 'games.jsonl').read_text().splitlines()
    return [json.loads(line) for line in rows if line.strip()
            and json.loads(line)['game']['status'] == 'completed']


def per_seed_contrast(rows):
    """Per seed: (slot-0 wins minus slot-1 wins) divided by that seed's rotations."""
    by = {}
    for r in rows:
        by.setdefault(r['seed'], []).append((r['winner_slot'] == 0) - (r['winner_slot'] == 1))
    return {seed: sum(v) / len(v) for seed, v in by.items()}


def interval(values):
    xs = list(values)
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / max(1, len(xs) - 1))
    se = sd / math.sqrt(len(xs))
    return {'mean': mean, 'se': se, 'low': mean - 1.96 * se, 'high': mean + 1.96 * se,
            'seeds': len(xs)}


def fmt(c):
    return f"{c['mean']:+.3f} (95% interval {c['low']:+.3f} to {c['high']:+.3f}, {c['seeds']} seeds)"


def slot_of_seat(row, seat_index):
    return row['slots'].index(seat_index)


def diagnostics(rows, slot):
    """Per-game means for one slot, plus the pooled mean hand size at the roll."""
    per_game = {k: [] for k in DIAGNOSTICS}
    hand_sum = 0
    hand_count = 0
    decisions = 0
    decision_ms = 0.0
    points = []
    wins = 0
    for r in rows:
        seat_index = r['slots'].index(slot)
        s = r['game']['seats'][seat_index]
        for k in DIAGNOSTICS:
            per_game[k].append(s.get(k, 0))
        hand_sum += s.get('hand_at_roll_sum', 0)
        hand_count += s.get('hand_at_roll_count', 0)
        decisions += s['decisions']
        decision_ms += s['decision_ms']
        points.append(s['points'])
        wins += r['winner_slot'] == slot
    n = len(rows)
    out = {k: sum(v) / n for k, v in per_game.items()}
    out['hand_at_roll'] = hand_sum / hand_count if hand_count else None
    out['mean_decision_ms'] = decision_ms / decisions if decisions else None
    out['mean_points'] = sum(points) / n
    out['wins'] = wins
    out['games'] = n
    return out


def main():
    write_asset = '--asset' in sys.argv
    pairs = {}
    for experiment, (stage, arm, half) in COHORTS.items():
        found = latest_run(experiment)
        if not found:
            continue
        _, run_id, summary = found
        rows = games(run_id)
        pairs.setdefault((stage, arm), {})[half] = {
            'experiment': experiment, 'run': run_id, 'rows': rows, 'summary': summary,
            'contrast': per_seed_contrast(rows)}

    results = {}
    for (stage, arm), halves in sorted(pairs.items()):
        if set(halves) != {'A', 'B'}:
            print(f'{stage} {arm}: waiting for half {sorted(set("AB") - set(halves))}')
            continue
        a, b = halves['A'], halves['B']
        if set(a['contrast']) != set(b['contrast']):
            print(f'{stage} {arm}: halves disagree on seeds; skipped')
            continue
        seeds = sorted(a['contrast'])
        effect = interval((a['contrast'][s] - b['contrast'][s]) / 2 for s in seeds)
        seating = interval((a['contrast'][s] + b['contrast'][s]) / 2 for s in seeds)
        # Candidate sits in slot 0 in half A and slot 1 in half B; pool the two views.
        cand = diagnostics(a['rows'], 0)
        ctrl = diagnostics(a['rows'], 1)
        cand_b = diagnostics(b['rows'], 1)
        ctrl_b = diagnostics(b['rows'], 0)
        pooled = {}
        for k in list(DIAGNOSTICS) + ['mean_points']:
            pooled[k] = ((cand[k] * cand['games'] + cand_b[k] * cand_b['games'])
                         / (cand['games'] + cand_b['games']),
                         (ctrl[k] * ctrl['games'] + ctrl_b[k] * ctrl_b['games'])
                         / (ctrl['games'] + ctrl_b['games']))
        hand = None
        if cand['hand_at_roll'] is not None:
            hand = (cand['hand_at_roll'], cand_b['hand_at_roll'], ctrl['hand_at_roll'],
                    ctrl_b['hand_at_roll'])
        decision = ((cand['mean_decision_ms'] + cand_b['mean_decision_ms']) / 2,
                    (ctrl['mean_decision_ms'] + ctrl_b['mean_decision_ms']) / 2)
        wins = (cand['wins'] + cand_b['wins'], ctrl['wins'] + ctrl_b['wins'])
        results.setdefault(arm, {})[stage] = {
            'effect': effect, 'seating': seating, 'wins': wins, 'pooled': pooled,
            'hand_at_roll': hand, 'decision_ms': decision,
            'runs': (a['run'], b['run']), 'experiments': (a['experiment'], b['experiment'])}
        print(f"{stage} {arm}: effect {fmt(effect)}; seating {fmt(seating)}")
        print(f"    wins candidate {wins[0]} / control {wins[1]} of "
              f"{cand['games'] + cand_b['games']}; runs {a['run'][:8]} + {b['run'][:8]}")
        print(f"    decision ms candidate {decision[0]:.1f}, control {decision[1]:.1f} "
              f"(ratio {decision[0] / decision[1]:.2f})")
        for k in ['cards_discarded', 'turns_over_limit', 'times_robbed', 'bank_trades']:
            print(f"    {k}: candidate {pooled[k][0]:.2f}, control {pooled[k][1]:.2f} per game")
        if hand:
            print(f"    mean hand size at the roll: candidate {(hand[0] + hand[1]) / 2:.2f}, "
                  f"control {(hand[2] + hand[3]) / 2:.2f}")

    print()
    pooled_l1 = {}

    def effect_terms(stage, arm):
        halves = pairs[(stage, arm)]
        return [(halves['A']['contrast'][s] - halves['B']['contrast'][s]) / 2
                for s in sorted(halves['A']['contrast'])]

    for arm in ARMS:
        stages = results.get(arm, {})
        l1 = [s for s in ('stage1', 'stage2') if s in stages]
        if len(l1) == 2:
            # After-the-fact pooling of the per-seed effect terms over both L1 pairs.
            terms = [t for stage in l1 for t in effect_terms(stage, arm)]
            pooled = interval(terms)
            pooled_l1[arm] = pooled
            print(f"{arm} pooled L1 over 128 seeds (after-the-fact pooling): {fmt(pooled)}")
    if pooled_l1:
        print()
        for arm, c in pooled_l1.items():
            triggers = c['mean'] > 0 and -0.03 <= c['low'] <= 0.03
            print(f"{arm}: stage-4 extension {'TRIGGERED' if triggers else 'not triggered'} "
                  f"(pooled L1 mean {c['mean']:+.3f}, lower bound {c['low']:+.3f})")

    # Final pooled estimates after any extension (after-the-fact pooling).
    print()
    for arm in ARMS:
        stages = results.get(arm, {})
        l1_stages = [s for s in ('stage1', 'stage2', 'stage4l1') if s in stages]
        l2_stages = [s for s in ('stage3', 'stage4l2') if s in stages]
        if l1_stages:
            terms = [t for stage in l1_stages for t in effect_terms(stage, arm)]
            print(f"{arm} pooled builders lineup over {len(terms)} seeds "
                  f"(after-the-fact pooling): {fmt(interval(terms))}")
        if l2_stages:
            terms = [t for stage in l2_stages for t in effect_terms(stage, arm)]
            print(f"{arm} pooled population lineup over {len(terms)} seeds "
                  f"(after-the-fact pooling): {fmt(interval(terms))}")
        if l1_stages and l2_stages:
            terms = [t for stage in l1_stages + l2_stages for t in effect_terms(stage, arm)]
            print(f"{arm} pooled over all {len(terms)} seeds "
                  f"(after-the-fact pooling): {fmt(interval(terms))}")
            # The registered browser rule: pooled effect at least +0.03 with the interval
            # excluding zero, and mean decision time within 25 percent of the control's.
            c = interval(terms)
            ratios = [stages[s]['decision_ms'][0] / stages[s]['decision_ms'][1]
                      for s in l1_stages + l2_stages]
            ratio = sum(ratios) / len(ratios)
            worth = c['mean'] >= 0.03 and c['low'] > 0 and ratio <= 1.25
            print(f"    browser rule: pooled {c['mean']:+.3f} with lower bound {c['low']:+.3f}, "
                  f"mean decision-time ratio {ratio:.2f} -> "
                  f"{'worth the browser' if worth else 'NOT worth the browser'}")

    if '--json' in sys.argv:
        dump = {}
        for arm, stages in results.items():
            dump[arm] = {}
            for stage, r in stages.items():
                halves = pairs[(stage, arm)]
                half_rows = {}
                for half, h in halves.items():
                    cand_slot = 0 if half == 'A' else 1
                    d = diagnostics(h['rows'], cand_slot)
                    dc = diagnostics(h['rows'], 1 - cand_slot)
                    half_rows[half] = {'run': h['run'], 'experiment': h['experiment'],
                                       'candidate_wins': d['wins'], 'control_wins': dc['wins'],
                                       'candidate_points': d['mean_points'],
                                       'control_points': dc['mean_points'],
                                       'candidate_ms': d['mean_decision_ms'],
                                       'control_ms': dc['mean_decision_ms']}
                dump[arm][stage] = {'effect': r['effect'], 'seating': r['seating'],
                                    'wins': r['wins'], 'runs': r['runs'],
                                    'experiments': r['experiments'],
                                    'decision_ms': r['decision_ms'],
                                    'pooled': {k: r['pooled'][k] for k in DIAGNOSTICS},
                                    'hand_at_roll': r['hand_at_roll'], 'halves': half_rows}
        Path('/tmp/opencode/hand-tables-results.json').write_text(json.dumps(dump, indent=1))
        print('wrote /tmp/opencode/hand-tables-results.json')

    if write_asset and results:
        from harness.records import write_json  # noqa: E402
        ticks, points = [], []
        x = 0
        TICK = {'stage1': 'development', 'stage2': 'confirmation', 'stage3': 'population',
                'stage4l1': 'extension, builders', 'stage4l2': 'extension, population'}
        for arm in ARMS:
            for stage in STAGES:
                if stage not in results.get(arm, {}):
                    continue
                c = results[arm][stage]['effect']
                ticks.append(f'{ARM_TITLES[arm]}, {TICK[stage]}')
                points.append({'x': x, 'y': round(c['mean'], 4),
                               'low': round(c['low'], 4), 'high': round(c['high'], 4)})
                x += 1
        if points:
            lo = min(p['low'] for p in points) - 0.03
            hi = max(p['high'] for p in points) + 0.03
            runs = sorted({r[:8] for arm in results.values() for s in arm.values() for r in s['runs']})
            data = {'schema': 1, 'kind': 'plot', 'variant': 'scatter',
                    'title': 'Hand-management switches under the learned leaf, seating-corrected',
                    'evidence': 'measured',
                    'source': ('Engine-arena swapped pairs of 512 games each on deterministic boards '
                               'played once per rotation; each point is the per-seed half-difference of '
                               'the two slot-0-minus-slot-1 contrasts of one pair, which removes the '
                               'turn-order seating term. Runs ' + ', '.join(runs) + '.'),
                    'caption': ('Each point is one swapped pair\u2019s seating-corrected effect in wins '
                                'per game with its 95% interval over boards.'),
                    'x': {'label': 'Arm and stage', 'min': 0, 'max': len(ticks) - 1, 'ticks': ticks},
                    'y': {'label': 'Wins per game, candidate minus control', 'min': round(lo, 2),
                          'max': round(hi, 2)},
                    'series': [{'label': 'Seating-corrected effect', 'points': points}]}
            write_json(ROOT / 'content/assets/hand-tables-effects.json', data)
            print('wrote content/assets/hand-tables-effects.json')


if __name__ == '__main__':
    main()
