"""Pooled effects of the opening/planner-tables study: the seating-corrected effect of
each swapped pair (half the difference of the two slot-0-minus-slot-1 contrasts, with
the seating term their half-sum) and the after-the-fact pooled estimate over the stage
seeds, each with a normal-approximation 95 percent interval over seeds."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (arm, stage, lineup): run with the candidate in slot 0, run with it in slot 1.
RUNS = {
    ('search', 'development', 'L1'): (
        'a9813bf7-dc0d-498b-b620-d948c6174b55', '1249d1a2-267b-40dc-bc65-fd2678080eef'),
    ('search', 'confirmation', 'L1'): (
        '797cd3dc-06c5-4581-81a2-c385567aecbf', 'a4173a36-ead4-4fee-af07-c001ccdb7b88'),
    ('search', 'population', 'L2'): (
        '795c3709-fcc1-42f5-96fb-fba6dda15dfe', '7cda63dd-b707-49b5-898d-8e54824fcc2b'),
    ('search', 'extension', 'L1'): (
        '7bcc5d5b-6878-4616-a9c7-584fdd99fb2d', '3dab2804-6437-4d06-a74b-f86b79374829'),
    ('search', 'extension', 'L2'): (
        '2447754d-31d4-41ee-b6be-768911c3e3ec', 'da5e566f-702b-40b9-9ee2-3a639ba8ea68'),
    ('covbal', 'development', 'L1'): (
        '365eaca0-57c4-4cb9-807e-49e9cc5ec45c', 'f3175601-94fe-41d3-b52b-370cd0b10206'),
    ('covbal', 'confirmation', 'L1'): (
        'e2e08bb9-afee-4948-8d84-9d048a700c43', '3343c9df-ff9b-44d3-aeba-c1530e6109dc'),
    ('covbal', 'population', 'L2'): (
        'b27c4f07-93df-4185-aa19-cd6b5f95f3bf', '2c77bc8b-22da-4490-ad01-45b57a29170f'),
    ('covbal', 'extension', 'L1'): (
        '92587c1d-13b2-48d6-9485-f17d374c2489', '2b380fba-16ab-4b57-b621-a487c7629ba2'),
    ('covbal', 'extension', 'L2'): (
        'ab8b1c67-d903-421f-9aac-c374c815cb79', '56f6f0f3-f402-4046-b6c9-b4372e03f7cc'),
    ('scarcity', 'development', 'L1'): (
        'c2866d05-4ca9-4545-9a10-ecdd1182a042', 'faed3f89-b5ce-4929-9c83-ad06ec974030'),
    ('scarcity', 'confirmation', 'L1'): (
        'd97d2a7b-3681-47ec-b516-ca968d1ae169', '3de8e8fa-2193-4239-8d8d-52bd3d0a99fe'),
    ('scarcity', 'population', 'L2'): (
        'c26c5f85-a645-4da3-b644-8b17d598733d', '9a09faae-b7ed-41cf-94fa-11cd3784a1a0'),
}


def per_seed(run):
    rows = [json.loads(line) for line in (ROOT / 'runs' / run / 'games.jsonl').read_text().splitlines() if line.strip()]
    seeds = {}
    for r in rows:
        if r['game']['status'] != 'completed':
            continue
        seeds.setdefault(r['seed'], []).append(r['winner_slot'])
    return {s: (sum(w == 0 for w in ws) - sum(w == 1 for w in ws)) / len(ws) for s, ws in seeds.items()}


def interval(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, [mean - 1.96 * se, mean + 1.96 * se]


def pair(run_a, run_b):
    a, b = per_seed(run_a), per_seed(run_b)
    effects = [(a[s] - b[s]) / 2 for s in sorted(a)]
    seating = [(a[s] + b[s]) / 2 for s in sorted(a)]
    effect, effect_ci = interval(effects)
    seat, seat_ci = interval(seating)
    return effect, effect_ci, seat, seat_ci, len(effects)


def main():
    pooled = {}
    for (arm, stage, lineup), (run_a, run_b) in RUNS.items():
        effect, ci, seat, seat_ci, n = pair(run_a, run_b)
        print(f'{arm:9s} {stage:12s} {lineup}: effect {effect:+.3f} ({ci[0]:+.3f} to {ci[1]:+.3f}) '
              f'seating {seat:+.3f} ({seat_ci[0]:+.3f} to {seat_ci[1]:+.3f}) over {n} seeds')
        pooled.setdefault((arm, lineup), []).append((run_a, run_b))
    for (arm, lineup), pairs in sorted(pooled.items()):
        effects, seating = [], []
        for run_a, run_b in pairs:
            a, b = per_seed(run_a), per_seed(run_b)
            effects += [(a[s] - b[s]) / 2 for s in sorted(a)]
            seating += [(a[s] + b[s]) / 2 for s in sorted(a)]
        effect, ci = interval(effects)
        seat, seat_ci = interval(seating)
        print(f'pooled {arm:9s} {lineup}: effect {effect:+.3f} ({ci[0]:+.3f} to {ci[1]:+.3f}) '
              f'seating {seat:+.3f} ({seat_ci[0]:+.3f} to {seat_ci[1]:+.3f}) over {len(effects)} seeds '
              f'(after-the-fact pooling over {len(pairs)} pairs)')


if __name__ == '__main__':
    main()
