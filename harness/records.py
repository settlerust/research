import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def write_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    os.replace(temporary, path)


def git_state(root):
    def git(*args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    return {'commit': git('rev-parse', 'HEAD'), 'dirty': git('status', '--porcelain') != ''}


def wilson(wins, total):
    if not total:
        return None
    z = 1.959963984540054
    p, denominator = wins / total, 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, centre - radius), min(1, centre + radius)]


def summarize(matches, lineup):
    # Each registered slot is a competitor, even if several use the same policy.
    finished = [m for m in matches if m['status'] == 'completed']
    rows = []
    for slot, policy in enumerate(lineup):
        appearances = [(m, m['slots'].index(slot)) for m in finished]
        wins = sum(m['winner'] == seat for m, seat in appearances)
        total = len(appearances)
        rows.append({
            'slot': slot, 'policy': policy, 'wins': wins, 'losses': total - wins,
            'completed': total, 'win_rate': wins / total if total else None,
            'wilson95': wilson(wins, total),
            'mean_points': sum(m['points'][seat] for m, seat in appearances) / total if total else None,
        })
    contrast = None
    if len(lineup) >= 2 and finished and all(m.get('seed') is not None for m in finished):
        by_seed = {}
        for m in finished:
            by_seed.setdefault(m['seed'], []).append(m)
        diffs = [sum((m['winner'] == m['slots'].index(0)) - (m['winner'] == m['slots'].index(1)) for m in games) / len(games)
                 for games in by_seed.values()]
        mean = sum(diffs) / len(diffs)
        sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / max(1, len(diffs) - 1))
        se = sd / math.sqrt(len(diffs))
        contrast = {'slots': [0, 1], 'seeds': len(diffs), 'mean_win_difference': mean, 'standard_error': se,
                    'interval95': [mean - 1.96 * se, mean + 1.96 * se]}
    return {
        'attempted': len(matches), 'completed': len(finished), 'paired_contrast': contrast,
        'incomplete': len(matches) - len(finished),
        'mean_turns': sum(m['turns'] for m in finished) / len(finished) if finished else None,
        'players': rows,
    }


def summary_table(summary):
    lines = ['| Slot / policy | Wins | Losses | Completed | Win rate | 95% Wilson interval | Mean points |',
             '| --- | ---: | ---: | ---: | ---: | --- | ---: |']
    for row in summary['players']:
        interval = row['wilson95']
        rate = f"{row['win_rate']:.1%}" if interval else '—'
        bounds = f'{interval[0]:.1%}–{interval[1]:.1%}' if interval else '—'
        points = f"{row['mean_points']:.2f}" if interval else '—'
        lines.append(f"| {row['slot']} / {row['policy']} | {row['wins']} | {row['losses']} | {row['completed']} | {rate} | {bounds} | {points} |")
    return '\n'.join(lines)
