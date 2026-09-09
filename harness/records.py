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


def contrast_text(summary):
    """Paired seed contrast sentence for a deterministic cohort, or an empty string."""
    c = summary.get('paired_contrast')
    if not c:
        return ''
    return (f"Paired contrast slot 0 minus slot 1: {c['mean_win_difference']:+.3f} wins per game over {c['seeds']} seeds "
            f"(95% interval {c['interval95'][0]:+.3f} to {c['interval95'][1]:+.3f}).\n\n")


def run_record(run_id, experiment, status, planned, summary, run_dir):
    """The compact Markdown record of one protocol run, derived from its retained summary."""
    paired = bool(summary.get('paired_contrast'))
    return (f'# Run {run_id}\n\nStatus: **{status}**. Experiment: `{experiment}`.'
            + (' Deterministic paired seeds, every seed played once per rotation.' if paired else '') + '\n\n'
            f"Planned: {planned}. Attempted: {summary['attempted']}. Completed: {summary['completed']}. "
            f"Incomplete: {summary['incomplete']}. Unplayed: {summary['unplayed']}.\n\n"
            + summary_table(summary) + '\n\n' + contrast_text(summary)
            + f"Manifest SHA-256: `{digest(run_dir / 'manifest.json')}`.\n\n"
            + f"Inventory SHA-256: `{digest(run_dir / 'inventory.json')}`.\n\n"
            + 'Artifacts are local under `runs/' + run_id + '/`; no remote durability is claimed until an archive receipt exists.\n\n'
            + 'Intervals are descriptive per competitor slot across completed games; outcomes within a game are dependent. '
            + 'Incomplete games are not losses. '
            + ('The paired contrast is the per-seed win difference between slots 0 and 1 with a normal-approximation interval over seeds.\n'
               if paired else 'Seat rotation does not pair random seeds.\n'))


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
