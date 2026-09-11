#!/usr/bin/env python3
"""Bias-free arm effects for the robber-targeting arms from same-orientation and swapped
cohorts on the same seeds. The arena asks trade recipients in seat order after the offerer,
which favours the seat placed one after the offerer: two identical searches differ by a
seating bias. For an arm worth `e` wins per game over an identical control, the
same-orientation contrast (arm in slot 0) is `e + b` and the swapped contrast (arm in slot
1) is `b - e`, so half the per-seed difference of the two contrasts is the bias-free effect
and half their sum is the bias. Values come from the retained run games.jsonl files.
"""
import argparse
import json
import math


def per_seed(path):
    diffs = {}
    rows = {}
    for line in open(path):
        row = json.loads(line)
        if row["game"]["status"] != "completed":
            continue
        seed = row["seed"]
        diff = (row["winner_slot"] == 0) - (row["winner_slot"] == 1)
        diffs[seed] = diffs.get(seed, 0) + diff
        rows[seed] = rows.get(seed, 0) + 1
    return {seed: d / rows[seed] for seed, d in diffs.items()}


def mean_interval(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, (mean - 1.96 * se, mean + 1.96 * se)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", action="append", required=True,
                        help="NAME=confirmation.jsonl,swapped.jsonl (same seeds)")
    args = parser.parse_args()
    print("| Arm | Same-orientation contrast | Swapped contrast | Bias-free effect (95% interval) | Seating bias |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for spec in args.arm:
        name, paths = spec.split("=", 1)
        same_path, swapped_path = paths.split(",", 1)
        same = per_seed(same_path)
        swapped = per_seed(swapped_path)
        seeds = sorted(set(same) & set(swapped))
        m1, _ = mean_interval([same[s] for s in seeds])
        m2, _ = mean_interval([swapped[s] for s in seeds])
        effects = [(same[s] - swapped[s]) / 2 for s in seeds]
        biases = [(same[s] + swapped[s]) / 2 for s in seeds]
        effect, interval = mean_interval(effects)
        bias, _ = mean_interval(biases)
        print(f"| {name} | {m1:+.3f} | {m2:+.3f} | {effect:+.3f} ({interval[0]:+.3f} to {interval[1]:+.3f}) | {bias:+.3f} |")


if __name__ == "__main__":
    main()
