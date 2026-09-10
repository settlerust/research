"""Turn one traced engine-arena decision into a `search` exhibit asset."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

RESOURCES = ['brick', 'lumber', 'wool', 'grain', 'ore']


def describe(action):
    if action is None:
        return 'wait'
    kind = action['type']
    if kind == 'trade':
        give = ' and '.join(f"{n} {RESOURCES[i]}" for i, n in enumerate(action['give']) if n)
        get = ' and '.join(f"{n} {RESOURCES[i]}" for i, n in enumerate(action['receive']) if n)
        return f"offer {give} for {get} to seat {action['other'] + 1}"
    if kind == 'bank_trade':
        give = ' and '.join(f"{n} {RESOURCES[i]}" for i, n in enumerate(action['give']) if n)
        get = ' and '.join(f"{n} {RESOURCES[i]}" for i, n in enumerate(action['receive']) if n)
        return f"bank {give} for {get}"
    if kind == 'build_road':
        return f"road on edge {action['edge']}"
    if kind in ('build_settlement', 'build_city'):
        return f"{kind.split('_')[1]} at {action['vertex']}"
    if kind == 'move_robber':
        victim = action.get('victim')
        return f"robber to hex {action['hex']}" + (f", rob seat {victim + 1}" if victim is not None else '')
    if kind == 'discard':
        return 'discard ' + ' and '.join(f"{n} {RESOURCES[i]}" for i, n in enumerate(action['resources']) if n)
    if kind == 'play_year_of_plenty':
        return 'year of plenty: ' + ' and '.join(f"{n} {RESOURCES[i]}" for i, n in enumerate(action['resources']) if n)
    if kind == 'play_monopoly':
        return f"monopoly on {action['resource']}"
    return kind.replace('_', ' ')


def outcome_label(group):
    parts = [f"settlement at {v}" for v in group['settlements']] + [f"city at {v}" for v in group['cities']]
    parts += [f"road on {e}" for e in group['roads']]
    if group['development']:
        parts.append(f"{group['development']} development card" + ('s' if group['development'] > 1 else ''))
    if group.get('won') is True:
        parts.append('wins the game')
    elif group.get('won') is False:
        parts.append('game lost')
    return ', '.join(parts) if parts else 'nothing more'


def outcomes_of(entry):
    """Explain-mode outcomes of a traced decision as the exhibit's display shape, or None."""
    levels = entry.get('outcomes')
    if not levels:
        return None
    out = []
    for level in levels:
        groups = [{'probability': round(g['probability'], 4), 'value': round(g['value'], 2), 'label': outcome_label(g),
                   'points': g['points'], 'turn': g['turn']} for g in level['groups'][:12] if g['probability'] > 0]
        if groups:
            out.append({'level': level['level'], 'other': round(max(0.0, level['other']), 4), 'groups': groups})
    return out or None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('games', help='games.jsonl produced by tournament --trace')
    parser.add_argument('topology', help='topology.json from a protocol run')
    parser.add_argument('name')
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--rotation', type=int, default=0)
    parser.add_argument('--turn', type=int, required=True)
    parser.add_argument('--chosen', help='Prefer the decision at that turn whose chosen action has this type')
    parser.add_argument('--title', required=True)
    parser.add_argument('--caption', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--policy', default='expectimax-v2', help='Policy name shown on the exhibit')
    args = parser.parse_args()
    rows = [json.loads(l) for l in Path(args.games).read_text().splitlines() if l.strip()]
    game = next(r for r in rows if r['seed'] == args.seed and r['rotation'] == args.rotation)
    entries = [e for e in game['game']['trace'] if e['turn'] == args.turn and e['phase']['type'] == 'main']
    if args.chosen:
        def kind(e):
            c = e['chosen']
            return (c.get('action') or {}).get('type') if c and c['type'] == 'act' else (c or {}).get('type')
        entries = [e for e in entries if kind(e) == args.chosen] or entries
    entry = max(entries, key=lambda e: len(e['candidates']))
    chosen = json.dumps(entry['chosen'], sort_keys=True)
    candidates = []
    for c in entry['candidates'][:8]:
        candidates.append({'label': describe(c['action']), 'value': round(c['value'], 2),
                           'chosen': json.dumps(c['command'], sort_keys=True) == chosen,
                           'contributions': {k: round(v, 2) for k, v in c['contributions'].items()}})
    if not any(c['chosen'] for c in candidates):
        candidates[0]['chosen'] = True
    levels = [{'level': i, 'nodes': n, 'afterstates': a} for i, (n, a) in enumerate(zip(entry.get('per_level_nodes', []), entry['per_level_afterstates'])) if i >= 1]
    statistics = {'transitions': entry['transitions'], 'leaves': entry['leaves'], 'scenarios': entry.get('scenarios', 0), 'transpositions': entry.get('transpositions', 0)}
    position = entry['position']
    position['players'] = [{k: v for k, v in p.items() if k != 'victory_cards' or v is not None} for p in position['players']]
    data = {'schema': 1, 'kind': 'search', 'title': args.title, 'caption': args.caption, 'evidence': 'measured',
            'source': args.source, 'policy': args.policy, 'seat': entry['seat'], 'turn': entry['turn'],
            'phase': entry['phase']['type'], 'depth': entry['depth'], 'timeMs': round(entry['ms'], 1),
            'topology': json.loads(Path(args.topology).read_text()), 'position': position, 'hand': entry['hand'],
            'candidates': candidates, 'levels': levels,
            'statistics': statistics}
    outcomes = outcomes_of(entry)
    if outcomes:
        data['outcomes'] = outcomes
    write_json(ROOT / 'content/assets' / f'{args.name}.json', data)
    print(ROOT / 'content/assets' / f'{args.name}.json', len(candidates), 'candidates')


if __name__ == '__main__':
    sys.exit(main())
