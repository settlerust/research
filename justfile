set dotenv-load := false
set positional-arguments := true

default:
    @just --list

# Build the existing Rust server and fast/eta policies (requires SETTLERS_SERVER_DIR or ../server).
setup:
    python3 -m harness.cli setup

# Foreground authoritative server; Ctrl-C stops it. Default: 127.0.0.1:5555.
server:
    python3 -m harness.cli server

doctor:
    python3 -m harness.cli doctor

policies:
    python3 -m harness.cli policies

# Example: just match fast eta legal-first eta --games 4
match *args:
    python3 -m harness.cli match "$@"

# Example: just register --players fast eta fast eta --games 40 --hypothesis '...' --decision-rule '...'
register *args:
    python3 -m harness.cli register "$@"

run experiment:
    python3 -m harness.cli run {{quote(experiment)}}

archive run destination:
    python3 -m harness.cli archive {{quote(run)}} {{quote(destination)}}

# Example: just publish RUN_UUID --match 0 --slug baseline-smoke
publish *args:
    python3 -m harness.cli publish "$@"

check:
    python3 -m unittest discover -s tests -v
    python3 scripts/check_repository.py
