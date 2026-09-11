#!/usr/bin/env python3
"""Share of robber placements that land on the points leader's best hex, per seat slot.

Reads one or more engine-arena games.jsonl files written with the robber-move diagnostic
(the arena records each placement with the mover, the hex, the victim, the points leader
among the mover's rivals, and that seat's highest-pip hex, cities counting double). Prints,
per seat slot, how many robber moves the seat made and how often the robber landed on that
leader's best hex or robbed the leader. A screen-level diagnostic, not evidence on its own.
"""
import argparse
import json


def rows(paths):
    for path in paths:
        with open(path) as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games", nargs="+", help="games.jsonl files")
    parser.add_argument("--slots", type=int, default=None, help="only these slot indexes")
    args = parser.parse_args()
    moves = {}
    obvious = {}
    robbed_leader = {}
    wins = {}
    games = {}
    for row in rows(args.games):
        slots = row["slots"]
        for slot in slots:
            games[slot] = games.get(slot, 0) + 1
        if row.get("winner_slot") is not None:
            wins[row["winner_slot"]] = wins.get(row["winner_slot"], 0) + 1
        for move in row["game"].get("robber_moves", []):
            slot = slots[move["player"]]
            moves[slot] = moves.get(slot, 0) + 1
            if move.get("leader_hex") is not None and move["hex"] == move["leader_hex"]:
                obvious[slot] = obvious.get(slot, 0) + 1
            if move.get("victim") is not None and move["victim"] == move["leader"]:
                robbed_leader[slot] = robbed_leader.get(slot, 0) + 1
    print("| Slot | Games | Wins | Robber moves | On the leader's best hex | Robbed the leader |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for slot in sorted(moves):
        if args.slots is not None and slot not in args.slots:
            continue
        n = moves[slot]
        share = obvious.get(slot, 0) / n if n else 0.0
        leader_share = robbed_leader.get(slot, 0) / n if n else 0.0
        print(
            f"| {slot} | {games.get(slot, 0)} | {wins.get(slot, 0)} | {n} | "
            f"{obvious.get(slot, 0)} ({share:.1%}) | {robbed_leader.get(slot, 0)} ({leader_share:.1%}) |"
        )


if __name__ == "__main__":
    main()
