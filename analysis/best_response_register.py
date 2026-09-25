"""Register the swapped pairs of study population/best-response and record their IDs in
analysis/best_response.json, which analysis/best_response_queue.sh runs and
analysis/best_response.py analyses.

Every pair is two registrations on the same deterministic boards: half A seats the candidate
in slot 0 and the control in slot 1, half B swaps them; the other two seats stay. Lineup L1
fills slots 2 and 3 with the ETA and fast builders; lineup L2 with a third frozen-tables
search and ETA, so the candidate meets two frozen seats. The frozen candidates are the best
validation points of the study's training arms (records/training/best-response/), copied to
artifacts/ntuple/best-response-ARM.bin with receipts under records/artifacts/.

    python3 analysis/best_response_register.py [PAIR ...]"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = 'population/best-response'
ARTIFACTS = '/home/keshav/settlers/research/artifacts/ntuple'
FROZEN = f'{ARTIFACTS}/hex-portfolio-main.bin'
def seat(path):
    return f'v2:{{"depth":2,"leaf":{{"tables":"{path}"}}}}'
BASE = seat(FROZEN)
CHALLENGER = seat(f'{ARTIFACTS}/best-response-challenger.bin')
CONTROL = seat(f'{ARTIFACTS}/best-response-control.bin')
POPULATION = seat(f'{ARTIFACTS}/best-response-population.bin')
L1 = ['eta', 'fast']
L2 = [BASE, 'eta']
DEV, CONF = '1400-1463', '1464-1527'

CONTRAST = ('Primary contrast: the seating-corrected effect of the candidate over the control, half the per-board '
            'difference of the two halves\' slot-0-minus-slot-1 win contrasts (analysis/seating_pair.py), with a '
            'normal 95% interval over the 64 boards; the half-sum is the seating term. All 256 games of each half '
            'complete. Decision-time ratio and play statistics (cities, cards, trades, robber moves) reported '
            'alongside. Development tier (engine arena).')
PAIRS = {
    'challenger-l2-dev': {
        'candidate': CHALLENGER, 'control': BASE, 'rest': L2, 'seeds': DEV, 'lineup': 'L2',
        'needs': ['best-response-challenger.bin'],
        'what': ('Exploitability at the population table. The challenger, warm-started from the frozen tables and '
                 'trained for 40,000 games against three seats drawn from {self:1, frozen tables:3} (only its own '
                 'seats learn), beats the frozen tables at depth 2 by more than +0.10 wins per game when the other '
                 'seats are a third frozen-tables search and ETA (L2), so the frozen tables\' self-play style is '
                 'exploitable by a player that has seen it.'),
        'rule': ('Support if the interval lies above zero and the estimate reaches +0.10; refutation if the interval '
                 'lies below +0.10 (no exploitable gain of that size; below zero, no gain at all); otherwise '
                 'inconclusive. ' + CONTRAST),
    },
    'challenger-l1-dev': {
        'candidate': CHALLENGER, 'control': BASE, 'rest': L1, 'seeds': DEV, 'lineup': 'L1',
        'needs': ['best-response-challenger.bin'],
        'what': ('Specialization check at the builder table. The same challenger\'s gain over the frozen tables '
                 'shrinks or vanishes when the other seats are the ETA and fast builders (L1) on the same boards as '
                 'the L2 pair: the effect is below +0.10 and smaller than at L2, which would show a specialized '
                 'exploit of the frozen tables rather than a generally stronger player.'),
        'rule': ('Support (specialization) if the L1 estimate is below +0.10 and the per-board difference of the L2 '
                 'pair\'s effect minus this pair\'s effect on the same boards has an interval above zero; refutation '
                 'if this pair\'s interval lies above +0.10 (the gain is general); otherwise inconclusive. '
                 + CONTRAST),
    },
    'control-l2-dev': {
        'candidate': CONTROL, 'control': BASE, 'rest': L2, 'seeds': DEV, 'lineup': 'L2',
        'needs': ['best-response-control.bin'],
        'what': ('The fine-tune\'s share. The control tables, warm-started from the frozen tables and trained for '
                 'the same 40,000 games at the same alpha in plain self-play (pool self), gain less over the frozen '
                 'tables at L2 than the challenger does on the same boards: the control\'s effect is below +0.10 '
                 'and below the challenger\'s, so the challenger\'s gain comes from the opponent change, not from '
                 'more training.'),
        'rule': ('Support if the control\'s estimate is below +0.10 and the per-board difference of the challenger '
                 'pair\'s effect minus this pair\'s effect has an interval above zero; refutation if this pair\'s '
                 'interval lies above +0.10; otherwise inconclusive. ' + CONTRAST),
    },
    'population-l1-conf': {
        'candidate': POPULATION, 'control': BASE, 'rest': L1, 'seeds': CONF, 'lineup': 'L1',
        'needs': ['best-response-population.bin'],
        'what': ('Remedy at the builder table. Tables warm-started from the frozen tables and trained for 60,000 '
                 'games on the mixed population {self:2, frozen tables:1, eta:0.5, fast:0.5} beat the frozen tables '
                 'at depth 2 by at least +0.03 wins per game with the ETA and fast builders (L1) on the confirmation '
                 'boards.'),
        'rule': ('Support if the interval lies above zero and the estimate reaches +0.03; refutation if the interval '
                 'lies below zero; otherwise inconclusive. ' + CONTRAST),
    },
    'population-l2-conf': {
        'candidate': POPULATION, 'control': BASE, 'rest': L2, 'seeds': CONF, 'lineup': 'L2',
        'needs': ['best-response-population.bin'],
        'what': ('Remedy at the population table. The same population-trained tables beat the frozen tables at '
                 'depth 2 by at least +0.03 wins per game with a third frozen-tables search and ETA (L2) on the '
                 'confirmation boards.'),
        'rule': ('Support if the interval lies above zero and the estimate reaches +0.03; refutation if the interval '
                 'lies below zero; otherwise inconclusive. ' + CONTRAST),
    },
    'population-vs-challenger-l2-conf': {
        'candidate': POPULATION, 'control': CHALLENGER, 'rest': L2, 'seeds': CONF, 'lineup': 'L2',
        'needs': ['best-response-population.bin', 'best-response-challenger.bin'],
        'what': ('Does the remedy close the gap. The population-trained tables against the frozen tables\' '
                 'challenger at L2 (a third frozen-tables search and ETA) on the confirmation boards: the '
                 'population tables give up less to the challenger than the frozen tables do, that is the effect of '
                 'the population tables over the challenger lies above -0.03.'),
        'rule': ('Support if the interval lies above -0.03; refutation if the interval lies below -0.10 (the '
                 'challenger exploits the population tables about as much as the frozen tables); otherwise '
                 'inconclusive. ' + CONTRAST),
    },
}


def register(seats, seeds, hypothesis, rule):
    out = subprocess.run([sys.executable, '-m', 'harness.engine', 'register', '--study', STUDY, '--seats', *seats,
                          '--seeds', seeds, '--rotations', '4', '--deterministic', '--hypothesis', hypothesis,
                          '--decision-rule', rule], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.strip().splitlines()[-1]


def main():
    registry_path = ROOT / 'analysis/best_response.json'
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {'base': BASE, 'pairs': []}
    done = {p['label'] for p in registry['pairs']}
    for label in sys.argv[1:] or list(PAIRS):
        if label in done:
            print(f'{label}: already registered')
            continue
        p = PAIRS[label]
        where = ('the population lineup (a third frozen-tables search in slot 2, ETA in slot 3)' if p['lineup'] == 'L2'
                 else 'the builder lineup (ETA in slot 2, fast in slot 3)')
        common = (f'{p["what"]} Lineup {p["lineup"]}, {where}, boards {p["seeds"]}, four rotations, deterministic. ')
        a = register([p['candidate'], p['control'], *p['rest']], p['seeds'],
                     common + 'Half A of the swapped pair: the candidate in slot 0, the control in slot 1; half B is registered next.',
                     p['rule'])
        b = register([p['control'], p['candidate'], *p['rest']], p['seeds'],
                     common + f'Half B of the swapped pair: the control in slot 0, the candidate in slot 1; the partner half A is experiment {a}.',
                     p['rule'])
        registry['pairs'].append({'label': label, 'lineup': p['lineup'], 'seeds': p['seeds'], 'candidate': p['candidate'],
                                  'control': p['control'], 'needs': p['needs'], 'half_a': a, 'half_b': b})
        print(f'{label:34} A {a} B {b}')
    registry_path.write_text(json.dumps(registry, indent=1) + '\n')


if __name__ == '__main__':
    main()
