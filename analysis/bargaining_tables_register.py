"""Register the swapped pairs of the bargaining switches under the learned leaf.

Each arm is the tables baseline seat plus one bargaining switch turned off; its control is the
baseline. Half A seats the arm in slot 0 and the control in slot 1, half B the reverse, on the
same seeds. Lineup L1 puts the ETA and fast builders in slots 2 and 3; lineup L2 puts a third
tables search in slot 2 and ETA in slot 3. Experiment IDs are appended to the registry JSON
that analysis/bargaining_tables.py reads.

    python3 analysis/bargaining_tables_register.py analysis/bargaining_tables.json STAGE [ARM ...]

STAGE is one of l2-800, l1-0, l1-800, l2-864, l1-864."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = '/home/keshav/settlers/research/artifacts/ntuple/hex-portfolio-main.bin'
BASE = f'v2:{{"depth":2,"leaf":{{"tables":"{TABLES}"}}}}'
ARMS = {
    'all-off': ('bargain', 'every bargaining mechanism off (plain acceptance and proposals, no threat costs, counters, or asks)'),
    'threat-off': ('threat_pricing', 'the threat premium on the margin and the partner-gain cost off'),
    'counters-off': ('counters', 'counters to open offers off'),
    'asks-off': ('asks', 'two-for-one asks to well-stocked partners off'),
    'stubborn': ('accept_asks', 'a stubborn seat that refuses any offer or counter asking it for more cards than it receives'),
}
STAGES = {
    'l2-800': ('L2', '800-863', [BASE, 'eta']),
    'l1-0': ('L1', '0-63', ['eta', 'fast']),
    'l1-800': ('L1', '800-863', ['eta', 'fast']),
    'l2-864': ('L2', '864-927', [BASE, 'eta']),
    'l1-864': ('L1', '864-927', ['eta', 'fast']),
}
RULE = ('All 256 games complete. The seating-corrected effect of the arm over the swapped pair (per-seed '
        'half-difference of the two slot-0-minus-slot-1 contrasts, analysis/seating_pair.py) has a 95% seed '
        'interval that excludes zero below (support: the mechanism helps under the tables), excludes zero above '
        '(refutation: the mechanism hurts), or neither (inconclusive). The half-sum is the seating term.')


def seat(switch):
    return f'v2:{{"depth":2,"leaf":{{"tables":"{TABLES}"}},"{switch}":false}}'


def register(seats, seeds, hypothesis, study='bargaining/tables-arms'):
    out = subprocess.run([sys.executable, '-m', 'harness.engine', 'register', '--study', study, '--seats', *seats,
                          '--seeds', seeds, '--rotations', '4', '--deterministic', '--hypothesis', hypothesis,
                          '--decision-rule', RULE], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.strip().splitlines()[-1]


def main():
    registry_path = Path(sys.argv[1])
    stage = sys.argv[2]
    arms = sys.argv[3:] or list(ARMS)
    lineup, seeds, rest = STAGES[stage]
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {'base': BASE, 'pairs': []}
    for arm in arms:
        switch, what = ARMS[arm]
        candidate = seat(switch)
        where = ('the population lineup (a third tables search in slot 2, ETA in slot 3)' if lineup == 'L2'
                 else 'the builder lineup (ETA in slot 2, fast in slot 3)')
        common = (f'Under the learned n-tuple leaf at depth 2, `{switch}: false` ({what}) loses to the unchanged '
                  f'tables baseline: the seating-corrected effect of the arm is negative, so the default mechanism '
                  f'helps under the tables as it did under the hand-written leaf. Lineup {lineup}, {where}, '
                  f'seeds {seeds}, four rotations, deterministic. ')
        a = register([candidate, BASE, *rest], seeds,
                     common + 'Half A of the swapped pair: the arm in slot 0, the control in slot 1; half B is registered next.')
        b = register([BASE, candidate, *rest], seeds,
                     common + f'Half B of the swapped pair: the control in slot 0, the arm in slot 1; the partner half A is experiment {a}.')
        registry['pairs'].append({'arm': arm, 'switch': switch, 'stage': stage, 'lineup': lineup, 'seeds': seeds,
                                  'half_a': a, 'half_b': b})
        print(f'{stage} {arm:12} A {a} B {b}')
    registry_path.write_text(json.dumps(registry, indent=1) + '\n')


if __name__ == '__main__':
    main()
