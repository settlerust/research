"""Endgame diagnostics from engine-arena game records: games the focal slot lost by exactly
one point, how often the final-points leader was robbed, and the final point spread between
the winner and the focal seat. Prints a compact table for one or more `games.jsonl` files."""
import argparse
import json
from pathlib import Path
import statistics


def load(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    return [r for r in rows if r['game'].get('status') == 'completed']


def diagnostics(rows, focal=0):
    lost_by_one = 0
    losses = 0
    spreads = []
    leader_robbed = []
    leader_share = []
    for r in rows:
        game = r['game']
        points = {r['slots'][i]: s['points'] for i, s in enumerate(game['seats'])}
        robbed = {r['slots'][i]: s['times_robbed'] for i, s in enumerate(game['seats'])}
        winner = r['winner_slot']
        spread = points[winner] - points[focal]
        if winner != focal:
            losses += 1
            if spread == 1:
                lost_by_one += 1
        spreads.append(spread)
        # The final-points leader is a public proxy for the leader the seats saw.
        leader = max(points, key=lambda slot: (points[slot], -slot))
        leader_robbed.append(robbed[leader])
        total = sum(robbed.values())
        if total:
            leader_share.append(robbed[leader] / total)
    return {
        'games': len(rows),
        'focal_wins': sum(1 for r in rows if r['winner_slot'] == focal),
        'losses': losses,
        'lost_by_exactly_one_point': lost_by_one,
        'mean_winner_minus_focal_points': statistics.mean(spreads) if spreads else None,
        'median_winner_minus_focal_points': statistics.median(spreads) if spreads else None,
        'mean_times_final_leader_robbed': statistics.mean(leader_robbed) if leader_robbed else None,
        'share_of_robberies_on_final_leader': statistics.mean(leader_share) if leader_share else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('games', nargs='+', help='games.jsonl files from engine-arena runs')
    parser.add_argument('--focal', type=int, default=0, help='slot the diagnostics centre on')
    args = parser.parse_args()
    keys = ['games', 'focal_wins', 'losses', 'lost_by_exactly_one_point',
            'mean_winner_minus_focal_points', 'median_winner_minus_focal_points',
            'mean_times_final_leader_robbed', 'share_of_robberies_on_final_leader']
    for path in args.games:
        row = diagnostics(load(path), args.focal)
        print(path)
        for key in keys:
            value = row[key]
            print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")


if __name__ == '__main__':
    main()
