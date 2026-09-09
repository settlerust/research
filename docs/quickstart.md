---
title: "1. Connect to the game server"
summary: Start an authoritative server, check the connection, and understand the observation–decision–command loop.
---

# Connect your first agent

By the end of this tutorial, your agent will read its own game observation, choose a legal action, and play a complete game against computer policies. The server runs the rules, dice, trades, and scoring. Your policy supplies decisions.

## Start the server

Work from the research checkout. Install Python 3.11 or newer and `just`. The Python harness has no third-party dependencies. To build the bundled server and Rust opponents, install Rust and keep the server checkout alongside this one as `../server`.

```sh
# Only needed if the server checkout lives somewhere else:
export SETTLERS_SERVER_DIR=/path/to/settlers/server
just setup
just server
```

`just server` stays in the foreground at `http://127.0.0.1:5555`. Leave it running and open another terminal in the research checkout:

```sh
just doctor
just policies
```

The doctor checks the server connection and protocol. The policy list shows the available player commands. If you already have a server, set `SETTLERS_SERVER_URL` to its address instead of starting another one. Remote `fast` and `eta` opponents still need their locally built executables; a lineup made entirely of stdio policies needs only Python and a reachable server.

## Follow one decision

1. The harness creates an agent research table and a separate identity for each seat.
2. It sends your process that seat's observation, board topology, and newly delivered events.
3. Your process returns a command such as rolling, building a road, or offering a trade.
4. The harness submits it with the observed version and a request ID. The server validates and applies it.
5. Your next observation shows the result. Continue until the server declares a winner.

Your agent can remember earlier observations and messages. It can see its own hand and public information about opponents. A spectator replay is for people inspecting a game; it must never be used as an agent's input.

## Check the connection before coding

```sh
just match fast eta fast eta --games 4
```

The harness rotates the lineup through the seats and prints completion counts and outcomes. This first run checks the setup. Four games are too few to rank these policies. If a match fails, the schedule stops and retains the reason so you can fix the problem before continuing.

Continue to [2. Write your first policy](protocol.md).
