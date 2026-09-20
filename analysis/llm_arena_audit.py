"""Independently audit a finished arena series from its immutable journals.

Writes a compact local analysis, never modifies game records or invokes models.
Usage: python3 analysis/llm_arena_audit.py SERIES OUTPUT_JSON
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
from statistics import median


def digest(path):
    with path.open("rb") as stream:
        value = sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def wilson(wins, total):
    z = 1.959963984540054
    p = wins / total
    denominator = 1 + z * z / total
    middle = (p + z * z / (2 * total)) / denominator
    radius = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, middle - radius), min(1, middle + radius)]


def audit(series):
    plan = json.loads((series / "plan.json").read_text())
    state = json.loads((series / "state.json").read_text())
    assert state.get("finishedAt") and len(plan["games"]) == len(state["games"])
    totals = defaultdict(Counter)
    latency = defaultdict(list)
    inventory, rounds, conversations, notes, errors = [], [], [], [], []
    all_closures = Counter()
    for schedule, recorded in zip(plan["games"], state["games"], strict=True):
        config, expected = schedule["config"], recorded["summary"]
        game_id = config["id"]
        assert recorded["id"] == game_id and recorded["status"] == "completed"
        names = [player["name"] for player in config["players"]]
        counters = [Counter() for _ in names]
        requests, offers, closures = {}, {}, Counter()
        result, view, won, traded, elapsed, last_version = None, None, [], 0, 0, -1
        result_sequence = None
        for count, line in enumerate((series / f"{game_id}.journal.jsonl").open()):
            row = json.loads(line)
            payload = json.loads(row["payload"])
            assert row["sequence"] == count and row["elapsed_ms"] >= elapsed
            elapsed = row["elapsed_ms"]
            kind, seat = row["kind"], row["seat"]
            metric = counters[seat] if seat >= 0 else Counter()
            if kind == "metadata":
                assert payload["config"] == config
            elif kind == "snapshot":
                view = payload["view"]
                if view.get("opening"):
                    assert view["opening"]["order"] == schedule["turnOrder"]
            elif kind == "result":
                assert result is None
                result = payload
                result_sequence = count
            elif kind == "model_request":
                assert payload["request"]["model"] == config["players"][seat]["model"]
                requests[payload["requestId"]] = (seat, payload["mode"], payload.get("purpose", "decision"), elapsed)
                if payload.get("purpose", "decision") == "decision":
                    metric["decisionRequests"] += 1
            elif kind == "model_response":
                request_seat, mode, purpose, started = requests[payload["requestId"]]
                assert request_seat == seat and row["visibility"] == "spectators"
                response = payload["response"]
                usage = response.get("usage") or {}
                metric["promptTokens"] += usage.get("prompt_tokens", 0)
                metric["completionTokens"] += usage.get("completion_tokens", 0)
                metric["reasoningTokensReported"] += (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
                metric["usageMissingResponses"] += int(not usage)
                metric["outputLimitResponses"] += int(any(c.get("finish_reason") == "length" for c in response.get("choices", [])))
                if purpose == "decision":
                    metric["decisionResponses"] += 1
                    latency[names[seat]].append((elapsed - started) / 1000)
                    metric[mode + "CompletionTokens"] += usage.get("completion_tokens", 0)
            elif kind == "error":
                source = payload["source"]
                metric["errorSource:" + source] += 1
                if source != "cancelled_inference" and payload.get("requestId") in requests:
                    _, mode, purpose, _ = requests[payload["requestId"]]
                    metric["compactionErrors" if purpose == "compaction" else mode + "Errors"] += 1
            elif kind == "tool_result" and payload["result"].get("error"):
                message = str(payload["result"]["error"])
                metric["toolErrors"] += 1
                errors.append(dict(round=schedule["ordinal"], sequence=count, player=names[seat], message=message))
            elif kind == "note":
                metric["notes"] += 1
                notes.append(dict(round=schedule["ordinal"], sequence=count, player=names[seat], **payload))
            elif kind == "chat":
                metric["chats"] += 1
                conversations.append(dict(round=schedule["ordinal"], sequence=count, player=names[seat], **payload))
            elif kind == "baseline_decision":
                metric["baselineDecisions"] += 1
            elif kind == "game_events":
                assert payload["sequence"] > last_version
                last_version = payload["sequence"]
                for event in payload["events"]:
                    if event["type"] == "trade_offered":
                        offer = event["offer"]
                        assert offer["id"] not in offers
                        offers[offer["id"]] = offer
                        counters[offer["from"]]["offers"] += 1
                    elif event["type"] == "trade_closed":
                        closures[event["reason"]] += 1
                        if event["reason"] == "accepted":
                            offer = offers[event["offer_id"]]
                            counters[offer["from"]]["acceptedOffers"] += 1
                            counters[event["winner"]]["offersAcceptedFromOthers"] += 1
                    elif event["type"] == "rule":
                        rule = event["event"]
                        if rule["type"] == "timed_out":
                            counters[rule["player"]]["engineTimeouts"] += 1
                        elif rule["type"] == "traded":
                            traded += 1
                        elif rule["type"] == "won":
                            won.append(rule)
        assert result and view and result["status"] == "completed"
        winner = result["winner"]
        assert view["game"]["phase"] == {"type": "finished", "winner": winner}
        assert len(won) == 1 and won[0]["player"] == winner and won[0]["points"] >= config["points"]
        assert result["players"] == view["game"]["players"]
        assert len(offers) == sum(closures.values()) and traded == closures["accepted"]
        assert result["turn"] == expected["turn"] and count + 1 == expected["events"]
        assert ("expert:" if config["players"][winner]["kind"] == "expert" else "") + config["players"][winner]["model"] == expected["winner"]
        points = [player["points"] for player in result["players"]]
        for player in expected["players"]:
            seat = player["seat"]
            assert player["points"] == points[seat]
            assert player["startingPosition"] == schedule["turnOrder"].index(seat) + 1
            place = 1 if seat == winner else 2 + sum(points[other] > points[seat] for other in range(4) if other != winner) + (sum(points[other] == points[seat] for other in range(4) if other != winner) - 1) / 2
            assert place == player["place"]
            for key in ["promptTokens", "completionTokens", "decisionRequests", "decisionResponses", "activeErrors", "spectateErrors", "compactionErrors", "engineTimeouts", "toolErrors", "notes", "baselineDecisions"]:
                assert counters[seat][key] == player[key], (game_id, seat, key)
            counters[seat].update(games=1, wins=int(seat == winner), points=points[seat], place=place)
            counters[seat][f"startingPosition:{player['startingPosition']}"] += 1
            totals[names[seat]].update(counters[seat])
        for suffix in ["journal.jsonl", "parquet", "viewer.parquet", "summary.json"]:
            path = series / f"{game_id}.{suffix}"
            file_hash = digest(path)
            if suffix == "parquet":
                assert file_hash == recorded["parquetSha256"]
            elif suffix == "viewer.parquet":
                public = Path(plan["publishDirectory"]) / f"{game_id}.parquet"
                assert file_hash == recorded["replaySha256"] == digest(public)
                assert path.stat().st_size == recorded["replayBytes"] == public.stat().st_size
            inventory.append(dict(path=path.name, sha256=file_hash, bytes=path.stat().st_size))
        all_closures.update(closures)
        rounds.append(dict(round=schedule["ordinal"], id=game_id, winner=names[winner], turn=result["turn"],
                           seats=names, turnOrder=schedule["turnOrder"], points=points,
                           resultSequence=result_sequence, offers=len(offers), trades=traded,
                           closures=dict(closures), events=count + 1))
    standings = []
    for name, metric in totals.items():
        standings.append(dict(player=name, **metric, averagePlace=metric["place"] / metric["games"],
                              averagePoints=metric["points"] / metric["games"],
                              winInterval95=wilson(metric["wins"], metric["games"]),
                              medianDecisionSeconds=median(latency[name]) if latency[name] else None))
    standings.sort(key=lambda p: (-p["wins"], p["averagePlace"]))
    return dict(series=plan["id"], completed=len(rounds), finishedAt=state["finishedAt"],
                standings=standings, rounds=rounds, tradeClosures=dict(all_closures),
                conversations=conversations, notes=notes, toolErrors=errors, inventory=inventory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("series", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.series.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ["completed", "standings", "tradeClosures"]}, indent=2))
