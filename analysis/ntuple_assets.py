"""Plot assets from n-tuple training runs. Every number comes from a retained
`runs/ntuple/<arm>/progress.jsonl` row (development tier); the scripts reshape recorded
values and never compute a new claim."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402


def rows(arm, root):
    path = root / arm / 'progress.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def validations(arm, root):
    return [r['validation'] for r in rows(arm, root) if r.get('validation')]


def pilot_plot(arms, labels, root, title, caption):
    """Final validation margin per arm with its interval: tables minus hand leaf, wins per game."""
    points = []
    for i, arm in enumerate(arms):
        v = validations(arm, root)[-1]
        points.append({'x': i, 'y': round(v['margin'], 4), 'low': round(v['margin_interval'][0], 4), 'high': round(v['margin_interval'][1], 4)})
    lo = min(p['low'] for p in points) - 0.05
    hi = max(p['high'] for p in points) + 0.05
    source = 'Training runs under runs/ntuple/; the last validation tournament of each arm (24 fixed deterministic seeds, four rotations, depth 2, hand-written leaf in slot 1, ETA and fast builders).'
    return {'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'title': title, 'evidence': 'measured', 'source': source,
            'caption': caption, 'x': {'label': 'Layout', 'min': 0, 'max': len(arms) - 1, 'ticks': labels},
            'y': {'label': 'Wins per game, tables minus hand leaf', 'min': round(min(lo, -0.05), 2), 'max': round(max(hi, 0.05), 2)},
            'series': [{'label': 'Validation margin after the pilot budget', 'points': points}], 'reference': {'y': 0, 'label': 'no difference'}}


def curve_plot(arm, root, title, caption, direct=True):
    """Validation margin against games trained, for one arm."""
    vs = validations(arm, root)
    step = max(1, len(vs) // 144 + (len(vs) % 144 > 0))
    vs = vs[::step]
    series = [{'label': 'Tables as the depth-2 leaf', 'points': [
        {'x': round(v['games_trained'] / 1000, 1), 'y': round(v['margin'], 4), 'low': round(v['margin_interval'][0], 4),
         'high': round(v['margin_interval'][1], 4)} for v in vs]}]
    if direct and all(v.get('direct_margin') is not None for v in vs):
        series.append({'label': 'Tables played one ply', 'points': [
            {'x': round(v['games_trained'] / 1000, 1), 'y': round(v['direct_margin'], 4)} for v in vs]})
    ys = [p.get('low', p['y']) for s in series for p in s['points']] + [p.get('high', p['y']) for s in series for p in s['points']]
    xmax = max(p['x'] for s in series for p in s['points'])
    return {'schema': 1, 'kind': 'plot', 'variant': 'line', 'title': title, 'evidence': 'measured',
            'source': f'Training run runs/ntuple/{arm}; every validation point is a tournament on fixed deterministic seeds against the hand-written leaf in the same search with the two builders.',
            'caption': caption, 'x': {'label': 'Self-play games trained (thousands)', 'min': 0, 'max': float(int(xmax) + 1)},
            'y': {'label': 'Wins per game, tables minus hand leaf', 'min': round(min(ys) - 0.05, 2), 'max': round(max(ys) + 0.05, 2)},
            'series': series, 'reference': {'y': 0, 'label': 'no difference'}}


def wins_plot(arm, root, title, caption):
    vs = validations(arm, root)
    step = max(1, len(vs) // 144 + (len(vs) % 144 > 0))
    vs = vs[::step]
    keys = [('tables_wins', 'Tables as the depth-2 leaf'), ('hand_wins', 'Hand-written leaf, depth 2'), ('eta_wins', 'ETA builder'), ('fast_wins', 'Fast builder')]
    series = [{'label': label, 'points': [{'x': round(v['games_trained'] / 1000, 1), 'y': round(v[k] / max(1, v['completed']), 4)} for v in vs]} for k, label in keys]
    xmax = max(p['x'] for s in series for p in s['points'])
    return {'schema': 1, 'kind': 'plot', 'variant': 'line', 'title': title, 'evidence': 'measured',
            'source': f'Training run runs/ntuple/{arm}; per-slot win share of each validation tournament.',
            'caption': caption, 'x': {'label': 'Self-play games trained (thousands)', 'min': 0, 'max': float(int(xmax) + 1)},
            'y': {'label': 'Share of validation games won', 'min': 0, 'max': 1}, 'series': series}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['pilot', 'curve', 'wins'])
    parser.add_argument('name')
    parser.add_argument('--root', default=str(ROOT / 'runs/ntuple'))
    parser.add_argument('--arm', action='append', default=[], help='ARM or ARM=Label')
    parser.add_argument('--title', required=True)
    parser.add_argument('--caption', required=True)
    parser.add_argument('--no-direct', action='store_true')
    args = parser.parse_args()
    root = Path(args.root)
    arms = [a.split('=')[0] for a in args.arm]
    labels = [a.split('=', 1)[1] if '=' in a else a for a in args.arm]
    if args.kind == 'pilot':
        data = pilot_plot(arms, labels, root, args.title, args.caption)
    elif args.kind == 'curve':
        data = curve_plot(arms[0], root, args.title, args.caption, direct=not args.no_direct)
    else:
        data = wins_plot(arms[0], root, args.title, args.caption)
    write_json(ROOT / 'content/assets' / f'{args.name}.json', data)
    print(ROOT / 'content/assets' / f'{args.name}.json')
