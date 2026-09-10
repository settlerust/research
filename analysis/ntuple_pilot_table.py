"""Markdown table of a training pilot: per arm, the last validation point and the best one."""
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
rows = []
for arm in sorted(p for p in root.iterdir() if p.is_dir()):
    progress = arm / 'progress.jsonl'
    if not progress.exists():
        continue
    vals = [json.loads(l)['validation'] for l in progress.read_text().splitlines() if l.strip() and json.loads(l).get('validation')]
    if not vals:
        continue
    last, best = vals[-1], max(vals, key=lambda v: v['margin'])
    rows.append((arm.name, last, best, vals))
print('| Arm | Points | Last: tables / hand / ETA / fast | Last margin (95% interval) | Best margin (at games) |')
print('| --- | ---: | --- | --- | --- |')
for name, last, best, vals in rows:
    print(f"| {name} | {len(vals)} | {last['tables_wins']} / {last['hand_wins']} / {last['eta_wins']} / {last['fast_wins']} | "
          f"{last['margin']:+.3f} ({last['margin_interval'][0]:+.3f} to {last['margin_interval'][1]:+.3f}) | {best['margin']:+.3f} ({best['games_trained']:,}) |")
