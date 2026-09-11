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


if __name__ == "__main__":
    forest(
        [(f"{name} (0-63)", dev) for name, dev, _ in ARMS]
        + [(f"{name} (64-127)", confirmation) for name, _, confirmation in ARMS],
        "robber-targeting-contrasts",
    )
