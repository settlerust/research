"""Read learned n-tuple tables and decode what they hold. The file format is the server's
CTNTUP01 layout (`crates/expectimax/src/ntuple/mod.rs`); the hex pattern index is
((canonical_corners * 6 + resource) * 6 + pips) * 2 + robber, where a single occupied corner
canonicalizes to its own corner code. Values are table contributions in win-probability units;
they are meaningful relative to one another, not as absolute probabilities."""
import argparse
import json
from pathlib import Path
import array
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

HEX_PATTERNS = 15_625 * 6 * 6 * 2
RESOURCES = ['brick', 'lumber', 'wool', 'grain', 'ore']
CORNERS = {'own_settlement': 1, 'own_city': 2, 'other_settlement': 3, 'other_city': 4}


def load(path):
    data = Path(path).read_bytes()
    assert data[:8] == b'CTNTUP01', 'not a CTNTUP01 file'
    n = struct.unpack_from('<I', data, 8)[0]
    spec = data[12:12 + n].decode()
    count = struct.unpack_from('<Q', data, 12 + n)[0]
    offset = 12 + n + 8 + 1
    weights = array.array('f')
    weights.frombytes(data[offset:offset + count * 4])
    if sys.byteorder != 'little':
        weights.byteswap()
    return spec, weights


def hex_heatmap(weights, corner, robber=False):
    """5x5 grid: rows resources, columns pips 1 to 5, one occupied corner and nothing else."""
    c = CORNERS[corner]
    grid = []
    for r in range(5):
        row = []
        for pips in range(1, 6):
            index = ((c * 6 + (r + 1)) * 6 + pips) * 2 + int(robber)
            row.append(float(weights[index]))
        grid.append(row)
    return grid


def heatmap_asset(path, corner, title, caption, source):
    spec, weights = load(path)
    assert spec.startswith('hex'), f'layout {spec} has no hex table first'
    grid = hex_heatmap(weights, corner)
    values = [v for row in grid for v in row]
    points = [{'x': pips, 'y': r, 'value': round(grid[r][pips], 4)} for r in range(5) for pips in range(5)]
    return {'schema': 1, 'kind': 'plot', 'variant': 'heatmap', 'title': title, 'evidence': 'measured', 'source': source,
            'caption': caption, 'x': {'label': 'Pips of the hex number', 'min': 0, 'max': 4, 'ticks': ['1', '2', '3', '4', '5']},
            'y': {'label': 'Resource', 'min': 0, 'max': 4, 'ticks': RESOURCES},
            'series': [{'label': f'Hex window value with one {corner.replace("_", " ")} and empty corners', 'points': points}],
            'color': {'label': 'Table entry (win-probability units)', 'min': round(min(values), 4), 'max': round(max(values), 4)}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tables')
    parser.add_argument('name')
    parser.add_argument('--corner', choices=list(CORNERS), default='own_settlement')
    parser.add_argument('--title', required=True)
    parser.add_argument('--caption', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    data = heatmap_asset(args.tables, args.corner, args.title, args.caption, args.source)
    write_json(ROOT / 'content/assets' / f'{args.name}.json', data)
    print(json.dumps(data['series'][0]['points'][:5]))


# ----- portfolio tables (layout hex,portfolio: hex table first, then the five portfolio tables) -----
PRODUCTION_PATTERNS = 16 ** 5
HAND_PATTERNS = 3_125 * 9 * 6 * 5
RACE_PATTERNS = 13 * 13 * 13 * 8


def portfolio_offsets(spec):
    families = spec.split(',')
    assert 'portfolio' in families, spec
    cursor = 0
    if 'hex' in families:
        cursor += HEX_PATTERNS
    if 'vertex' in families:
        cursor += 37 * 37 * 37 * 6 * 4 * 7
    if 'corner' in families:
        cursor += 37 * 37 * 37 * 6
    return {'production': cursor, 'hand': cursor + PRODUCTION_PATTERNS, 'race': cursor + PRODUCTION_PATTERNS + HAND_PATTERNS}


def production_lines(path, init=None):
    """Marginal value of production pips in one resource: the mean entry over every touched
    production profile with that many pips in that resource, averaging over the other four.
    A profile is touched when its entry differs from the initial share (untouched entries hold
    exactly the initialization value)."""
    spec, weights = load(path)
    base = portfolio_offsets(spec)['production']
    if init is None:
        init = float(weights[base])  # the all-zero profile never occurs in play and keeps the initial share
    sums = [[0.0] * 16 for _ in RESOURCES]
    counts = [[0] * 16 for _ in RESOURCES]
    for index in range(PRODUCTION_PATTERNS):
        v = float(weights[base + index])
        if v == init:
            continue
        rest = index
        digits = [0] * 5
        for r in range(4, -1, -1):
            digits[r] = rest % 16
            rest //= 16
        for r in range(5):
            sums[r][digits[r]] += v
            counts[r][digits[r]] += 1
    series = []
    for r, name in enumerate(RESOURCES):
        points = [{'x': pips, 'y': round(sums[r][pips] / counts[r][pips], 4)} for pips in range(16) if counts[r][pips] >= 20]
        series.append({'label': name, 'points': points})
    return series


def hand_lines(path, settlements_left=3, cities_left=4):
    """Value of holding k cards of one resource and nothing else, k 0 to 4, at a mid-game building count."""
    spec, weights = load(path)
    base = portfolio_offsets(spec)['hand']
    series = []
    for r, name in enumerate(RESOURCES):
        points = []
        for k in range(5):
            digits = [0] * 5
            digits[r] = k
            hand = 0
            for d in digits:
                hand = hand * 5 + d
            index = ((hand * 9 + k) * 6 + settlements_left) * 5 + cities_left
            points.append({'x': k, 'y': round(float(weights[base + index]), 4)})
        series.append({'label': name, 'points': points})
    return series


def race_grid(path, bucket=4):
    """Own points against the best opponent's public points, second opponent two behind, mid-game turn bucket."""
    spec, weights = load(path)
    base = portfolio_offsets(spec)['race']
    points = []
    for own in range(2, 10):
        for first in range(4, 10):
            second = max(first - 2, 0)
            index = ((own * 13 + first) * 13 + second) * 8 + bucket
            points.append({'x': first - 4, 'y': own - 2, 'value': round(float(weights[base + index]), 4)})
    return points


def line_asset(series, title, caption, source, xlabel):
    ys = [p['y'] for s in series for p in s['points']]
    xmax = max(p['x'] for s in series for p in s['points'])
    return {'schema': 1, 'kind': 'plot', 'variant': 'line', 'title': title, 'evidence': 'measured', 'source': source, 'caption': caption,
            'x': {'label': xlabel, 'min': 0, 'max': float(xmax)}, 'y': {'label': 'Table entry (win-probability units)', 'min': round(min(ys) - 0.02, 3), 'max': round(max(ys) + 0.02, 3)},
            'series': series}


def race_asset(points, title, caption, source):
    values = [p['value'] for p in points]
    return {'schema': 1, 'kind': 'plot', 'variant': 'heatmap', 'title': title, 'evidence': 'measured', 'source': source, 'caption': caption,
            'x': {'label': "Best opponent's public points", 'min': 0, 'max': 5, 'ticks': [str(i) for i in range(4, 10)]},
            'y': {'label': 'Own points', 'min': 0, 'max': 7, 'ticks': [str(i) for i in range(2, 10)]},
            'series': [{'label': 'Race table entry, mid-game, second opponent two points behind the best', 'points': points}],
            'color': {'label': 'Table entry (win-probability units)', 'min': round(min(values), 4), 'max': round(max(values), 4)}}
