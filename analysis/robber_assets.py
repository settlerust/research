"""Assets for the robber-targeting study: one forest plot of paired seed contrasts across the
three arms and their fresh-seed confirmations. Every value is copied from a retained run
summary; nothing here plays games."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

ARMS = [
    ("leader", "15173b9c-502e-4e5a-8037-8220bca77707", "247cadd4-561b-461a-9448-2e1f500735cb"),
    ("need", "6c2d07c6-e7f0-4f91-8e75-43e590f1b1f1", "af5f61b5-5edd-4e56-b9da-c5fef93d737e"),
    ("threat", "0c77ef63-6296-410b-a0c5-191d054e055a", "e36e5562-3fbf-45ce-92e4-cd7c845cc3e3"),
]


def latest_run(experiment):
    runs = []
    for manifest in (ROOT / "runs").glob("*/manifest.json"):
        data = json.loads(manifest.read_text())
        if data.get("experiment") == experiment and (manifest.parent / "summary.json").exists():
            summary = json.loads((manifest.parent / "summary.json").read_text())
            if summary.get("status") == "completed":
                runs.append((data["created_at"], manifest.parent.name, summary))
    if not runs:
        return None
    return sorted(runs)[-1]


def forest(experiments, name):
    points, ticks = [], []
    for label, experiment in experiments:
        run = latest_run(experiment)
        if not run:
            continue
        _, run_id, summary = run
        c = summary["paired_contrast"]
        points.append(
            {
                "x": len(ticks),
                "y": round(c["mean_win_difference"], 4),
                "low": round(c["interval95"][0], 4),
                "high": round(c["interval95"][1], 4),
            }
        )
        ticks.append(label)
    if not points:
        raise SystemExit("no completed runs found")
    lo = min(p["low"] for p in points) - 0.05
    hi = max(p["high"] for p in points) + 0.05
    data = {
        "schema": 1,
        "kind": "plot",
        "variant": "scatter",
        "title": "Robber-targeting contrasts",
        "evidence": "measured",
        "source": (
            "Engine-arena cohorts under containment/robber-targeting: the arm in slot 0 against "
            "the unchanged depth-2 control in slot 1 with an ETA and a fast builder, 64 "
            "deterministic seeds each played once per rotation (256 games per point). Run IDs "
            "are listed in the robber-targeting report."
        ),
        "caption": "Each arm's paired win difference against the default robber shortlist, on the development seeds and on the fresh confirmation seeds.",
        "x": {"label": "Arm and seed range", "min": 0, "max": len(points) - 1, "ticks": ticks},
        "y": {
            "label": "Wins per game, arm minus control",
            "min": round(min(lo, -0.05), 2),
            "max": round(max(hi, 0.05), 2),
        },
        "series": [
            {"label": "Paired seed contrast (95% interval)", "points": points}
        ],
        "reference": {"y": 0, "label": "no difference"},
    }
    write_json(ROOT / "content/assets" / f"{name}.json", data)
    print(f"wrote content/assets/{name}.json with {len(points)} points")


def per_seed(path):
    """Per-seed slot-0 minus slot-1 win share over completed games."""
    diffs, counts = {}, {}
    for line in open(path):
        row = json.loads(line)
        if row["game"]["status"] != "completed":
            continue
        seed = row["seed"]
        diffs[seed] = diffs.get(seed, 0) + (row["winner_slot"] == 0) - (row["winner_slot"] == 1)
        counts[seed] = counts.get(seed, 0) + 1
    return {seed: d / counts[seed] for seed, d in diffs.items()}


def bias_free(confirmation_run, swapped_run):
    """Paired same-orientation and swapped contrasts cancel the arena seating term."""
    same = per_seed(ROOT / "runs" / confirmation_run / "games.jsonl")
    other = per_seed(ROOT / "runs" / swapped_run / "games.jsonl")
    seeds = sorted(set(same) & set(other))
    effects = [(same[s] - other[s]) / 2 for s in seeds]
    mean = sum(effects) / len(effects)
    sd = (sum((e - mean) ** 2 for e in effects) / max(1, len(effects) - 1)) ** 0.5
    se = sd / len(effects) ** 0.5
    return mean, (mean - 1.96 * se, mean + 1.96 * se)


if __name__ == "__main__":
    import sys

    ARMS = [
        ("leader", "15173b9c-502e-4e5a-8037-8220bca77707", "247cadd4-561b-461a-9448-2e1f500735cb", "a722f475-8cc5-4e2a-896b-4167764b2456", "10834001-571d-439c-83d2-9e31e1d5997b"),
        ("need", "6c2d07c6-e7f0-4f91-8e75-43e590f1b1f1", "af5f61b5-5edd-4e56-b9da-c5fef93d737e", "e214be7c-f184-4840-af3e-e82e7c23ffad", "165a28ac-94d3-4ebb-bbdf-989abb243bea"),
        ("threat", "0c77ef63-6296-410b-a0c5-191d054e055a", "e36e5562-3fbf-45ce-92e4-cd7c845cc3e3", "1d943a44-ffb0-459d-b487-733d26d50189", "cb91296b-ac8d-4f86-9ad6-5ba4d57af8ec"),
    ]
    points, ticks = [], []
    for name, dev, confirmation_experiment, confirmation_run, swapped_run in ARMS:
        for label, experiment in [(f"{name}, 0-63", dev), (f"{name}, 64-127", confirmation_experiment)]:
            run = latest_run(experiment)
            if not run:
                print(f"missing run for {experiment}", file=sys.stderr)
                continue
            _, _, summary = run
            c = summary["paired_contrast"]
            points.append({"x": len(ticks), "y": round(c["mean_win_difference"], 4),
                           "low": round(c["interval95"][0], 4), "high": round(c["interval95"][1], 4)})
            ticks.append(label)
        mean, interval = bias_free(confirmation_run, swapped_run)
        points.append({"x": len(ticks), "y": round(mean, 4),
                       "low": round(interval[0], 4), "high": round(interval[1], 4)})
        ticks.append(f"{name}, bias-free")
    data = {
        "schema": 1, "kind": "plot", "variant": "scatter", "title": "Robber-targeting contrasts",
        "evidence": "measured",
        "source": (
            "Engine-arena cohorts under containment/robber-targeting and "
            "containment/robber-targeting-bias: the arm against the unchanged depth-2 control "
            "with an ETA and a fast builder, 64 deterministic seeds each played once per "
            "rotation (256 games per point). The bias-free points pair the same-orientation "
            "confirmation with its swapped cohort on the same seeds. Run IDs are listed in the "
            "robber-targeting report."
        ),
        "caption": "Each arm's paired win difference with the arm in slot 0 on the development and fresh seeds, and the seating-bias-free effect from the swapped pairs.",
        "x": {"label": "Arm and measurement", "min": 0, "max": len(points) - 1, "ticks": ticks},
        "y": {"label": "Wins per game, arm minus control",
              "min": -0.1, "max": 0.2},
        "series": [{"label": "Paired seed contrast (95% interval)", "points": points}],
        "reference": {"y": 0, "label": "no difference"},
    }
    lo = min(p["low"] for p in points) - 0.05
    hi = max(p["high"] for p in points) + 0.05
    data["y"]["min"] = round(min(lo, -0.05), 2)
    data["y"]["max"] = round(max(hi, 0.05), 2)
    write_json(ROOT / "content/assets" / "robber-targeting-contrasts.json", data)
    print(f"wrote content/assets/robber-targeting-contrasts.json with {len(points)} points")
