"""Compare two engine-arena runs game by game: the equal-nodes pair of the transposition study.
Both runs play the same lineup on the same deterministic seeds; the second uses shared tables.
Writes records/structure/cache-compare-<run_a>-<run_b>.md and prints the summary."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def games(run):
    rows = [json.loads(l) for l in (ROOT / 'runs' / run / 'games.jsonl').read_text().splitlines() if l.strip()]
    return {(r['seed'], r['rotation']): r for r in rows}


def slot_stats(rows, slot):
    ms = decisions = hits = saved = transitions = 0
    for r in rows.values():
        seat = r['slots'].index(slot)
        rec = r['game']['seats'][seat]
        ms += rec['decision_ms']
        decisions += rec['decisions']
        transitions += rec['effort']['rollout_steps']
    return ms / max(1, decisions), transitions / max(1, decisions), decisions


def main(run_a, run_b):
    a, b = games(run_a), games(run_b)
    keys = sorted(set(a) | set(b))
    identical = mismatched = 0
    for k in keys:
        x, y = a.get(k), b.get(k)
        same = x and y and x['winner_slot'] == y['winner_slot'] and x['game']['turns'] == y['game']['turns'] and \
            [s['points'] for s in x['game']['seats']] == [s['points'] for s in y['game']['seats']] and x['game']['actions'] == y['game']['actions']
        identical += bool(same)
        mismatched += not same
    ms_a, tr_a, n_a = slot_stats(a, 0)
    ms_b, tr_b, n_b = slot_stats(b, 0)
    speedup = 1 - ms_b / ms_a if ms_a else 0
    text = (f"# Cache comparison {run_a[:8]} (fresh) against {run_b[:8]} (shared)\n\n"
            f"Games compared: {len(keys)}. Identical in winner, turns, points, and action count: {identical}. Different: {mismatched}.\n\n"
            f"| Run | Slot 0 decisions | Mean decision ms | Mean transitions per decision |\n| --- | ---: | ---: | ---: |\n"
            f"| `{run_a}` (fresh tables) | {n_a} | {ms_a:.1f} | {tr_a:.0f} |\n| `{run_b}` (shared tables) | {n_b} | {ms_b:.1f} | {tr_b:.0f} |\n\n"
            f"Decision time change with shared tables: {-speedup:+.1%}.\n")
    out = ROOT / 'records/structure' / f'cache-compare-{run_a[:8]}-{run_b[:8]}.md'
    out.write_text(text)
    print(text)
    return 0 if mismatched == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
