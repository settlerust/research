"""Asset for the search/settings-tables study: a forest plot of the seating-corrected
pooled effect of each arm under the learned tables. The pooled estimates are
after-the-fact poolings of the per-seed effects over both halves and stages,
recomputed from the retained runs by analysis/settings_tables.py; the numbers
below are its output for the completed program."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

# arm -> (label, pooled L1 effect, low, high, seeds)
POOLED_L1 = [
    ('scenarios 4', -0.392, -0.444, -0.339, '128'),
    ('scenarios 16', -0.026, -0.072, 0.019, '128'),
    ('samples 1', -0.109, -0.150, -0.069, '128'),
    ('samples 8', 0.045, 0.009, 0.081, '192'),
    ('leaf opponents', 0.031, -0.006, 0.068, '192'),
    ('counts only', -0.143, -0.188, -0.097, '128'),
    ('no proposals', -0.172, -0.211, -0.133, '128'),
    ('reciprocity', -0.073, -0.115, -0.031, '128'),
]


def main():
    points, ticks = [], []
    for label, effect, lo, hi, seeds in POOLED_L1:
        points.append({'x': len(points), 'y': round(effect, 4),
                       'low': round(lo, 4), 'high': round(hi, 4)})
        ticks.append(f'{label} ({seeds} seeds)')
    out = {'schema': 1, 'kind': 'plot', 'variant': 'scatter',
           'title': 'Seating-corrected effects under the learned tables',
           'evidence': 'measured',
           'source': 'Engine-arena swapped pairs of the search/settings-tables study: each point pools the '
                     'per-seed seating-corrected effects of one arm over its halves and stages (an after-the-fact '
                     'pooling; samples 8 and leaf opponents include the 864-927 extension, so 192 seeds), depth 2, '
                     'deterministic tapes, learned n-tuple leaf in both searches. Run IDs are in the report.',
           'caption': 'Each arm is the tables baseline plus one switch; intervals crossing zero are inconclusive, and inner scenarios is absent because it cannot bind at depth 2.',
           'x': {'label': 'Arm (pooled seeds)', 'min': 0, 'max': len(points) - 1, 'ticks': ticks},
           'y': {'label': 'Wins per game, candidate minus control (seating-corrected)',
                 'min': round(min(p['low'] for p in points) - 0.05, 2),
                 'max': round(max(p['high'] for p in points) + 0.05, 2)},
           'series': [{'label': 'Pooled seating-corrected effect (95% interval)', 'points': points}],
           'reference': {'y': 0, 'label': 'no difference'}}
    write_json(ROOT / 'content/assets' / 'settings-tables-effects.json', out)
    print('wrote content/assets/settings-tables-effects.json with', len(points), 'points')


if __name__ == '__main__':
    main()
