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
