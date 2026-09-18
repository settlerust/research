"""Publish compact competition metadata from the standalone arena's frozen evidence."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

MODELS = {
    "deepseek-ai/DeepSeek-V4-Pro-0813": "deepseek",
    "moonshotai/Kimi-K3": "kimi",
    "zai-org/GLM-5.3": "glm",
    "expert-ntuple": "expert",
}


def exhibit(series):
    plan = json.loads((series / "plan.json").read_text())
    state = json.loads((series / "state.json").read_text())
    config = plan["games"][0]["config"]
    checkpoint = json.loads((series / "runtime/vendor/manifest.json").read_text())["model"]["rawSha256"]
    participants = []
    for player in sorted(config["players"], key=lambda p: list(MODELS).index(p["model"])):
        participant = dict(id=MODELS[player["model"]], name=player["name"], model=player["model"],
                           provider=player.get("provider", "local"), input="text-and-image" if player["vision"] else "text",
                           kind=player["kind"])
        if player["kind"] == "expert":
            participant["search"] = dict(depth=player["depth"], milliseconds=player["searchMs"],
                                         nodeBudget=player["nodeBudget"], checkpointSha256=checkpoint)
        participants.append(participant)
    rounds = []
    for scheduled, recorded in zip(plan["games"], state["games"], strict=True):
        game = scheduled["config"]
        if game["id"] != recorded["id"]:
            raise ValueError("State does not match frozen schedule")
        status = recorded["status"]
        outcome = {"status": status}
        if status == "completed":
            summary = recorded["summary"]
            players = sorted(summary["players"], key=lambda p: p["seat"])
            winners = [p["seat"] for p in players if p.get("entrantId", p["model"]) == summary["winner"]]
            if len(winners) != 1 or summary["status"] != "completed":
                raise ValueError("A completed game needs one audited engine winner")
            outcome.update(winnerSeat=winners[0], points=[p["points"] for p in players],
                           turns=summary["turn"], durationSeconds=summary["elapsedSeconds"])
        elif status in ("failed", "incomplete"):
            outcome["reason"] = recorded.get("error") or "The game ended without an engine-recorded winner."
        elif status not in ("pending", "running"):
            raise ValueError("Unexpected match status")
        replay = None
        if recorded.get("published"):
            source = series / (game["id"] + ".parquet")
            public = Path(plan["publishDirectory"]) / source.name
            source_hash = sha256(source.read_bytes()).hexdigest()
            public_bytes = public.read_bytes()
            public_hash = sha256(public_bytes).hexdigest()
            if source_hash != recorded["parquetSha256"] or public_hash != recorded["replaySha256"]:
                raise ValueError("Replay hash disagrees with the audited source or published projection")
            if len(public_bytes) != recorded["replayBytes"]:
                raise ValueError("Published replay size changed")
            replay = dict(sha256=public_hash, bytes=len(public_bytes))
        rounds.append(dict(number=scheduled["ordinal"], gameId=game["id"], seed=game["seed"],
                           seats=[MODELS[p["model"]] for p in game["players"]],
                           openingOrder=scheduled["turnOrder"], turnOrder=scheduled["turnOrder"],
                           outcome=outcome, replay=replay))
    conditions = {name: config[key] for name, key in {
        "pointsToWin": "points", "turnSeconds": "turnSeconds", "spectatorSeconds": "spectatorSeconds",
        "spectateEveryTurns": "spectateEveryTurns", "contextWindowMoves": "contextWindowMoves",
        "contextRecentMoves": "contextRecentMoves", "contextMaxChars": "contextMaxChars",
        "searchMilliseconds": "searchMs", "maxTurns": "maxTurns", "maxRequests": "maxRequests",
        "maxTokens": "maxTokens", "reasoningEffort": "reasoningEffort", "turnTokenBudget": "turnTokenBudget",
        "spectatorTokenBudget": "spectatorTokenBudget", "turnRequestLimit": "turnRequestLimit",
    }.items()}
    conditions["concurrency"] = plan["concurrency"]
    return dict(schema=1, kind="competition", id=plan["id"], title=config["title"], date="2026-09-17",
                caption="Ten scheduled games on distinct boards with counterbalanced starting positions. Expert uses learned n-tuple expectimax; the other three players use the same LLM harness.",
                runtimeSha256=plan["runtimeHash"], replayBaseUrl="/replay", conditions=conditions,
                participants=participants, rounds=rounds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("series", type=Path)
    parser.add_argument("asset", type=Path)
    args = parser.parse_args()
    value = exhibit(args.series.resolve())
    temporary = args.asset.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(args.asset)
    print(json.dumps({"asset": str(args.asset), "rounds": len(value["rounds"]),
                      "completed": sum(r["outcome"]["status"] == "completed" for r in value["rounds"])}))
