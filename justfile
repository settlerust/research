set dotenv-load := false
set positional-arguments := true

default:
    @just --list

# Build the Rust server and remote search/builder runner (requires SETTLERS_SERVER_DIR or ../server).
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

# Example: just register --study ports/new-study --players fast eta fast eta --games 40 --hypothesis '...' --decision-rule '...'
register *args:
    python3 -m harness.cli register "$@"

# Example: just run EXPERIMENT_ID --parallel 8
run *args:
    python3 -m harness.cli run "$@"

archive run destination:
    python3 -m harness.cli archive {{quote(run)}} {{quote(destination)}}

# Example: just publish RUN_UUID --match 0 --slug baseline-smoke
publish *args:
    python3 -m harness.cli publish "$@"

# Build the offline engine arena in the server checkout (requires SETTLERS_SERVER_DIR or ../server).
build-arena:
    python3 -m harness.cli setup
    cargo build --release --locked -p settlers-arena --manifest-path "${SETTLERS_SERVER_DIR:-../server}/Cargo.toml"

# Example: just engine-register --study search/expectimax-v2 --seats v2 eta fast eta --seeds 0-63 --hypothesis '...' --decision-rule '...'
engine-register *args:
    python3 -m harness.engine register "$@"

# Paired-seed engine tournament for a registered engine experiment (development tier).
engine-run experiment:
    python3 -m harness.engine run {{quote(experiment)}}

# Decompress the committed frozen tables (tables/*.xz) into artifacts/ntuple/ and verify SHA-256.
tables:
    python3 scripts/unpack_tables.py

check:
    python3 -m unittest discover -s tests -v
    python3 scripts/check_repository.py
    python3 -m harness.notebook check

# Create an approach-owned investigation, or log/SLUG for cross-cutting work.
study *args:
    python3 -m harness.notebook study "$@"

# Refresh the experiment log, approach pages, and roadmap from filed studies.
notebook:
    python3 -m harness.notebook sync

# Validate filed evidence and the actual MDX/assets used by the web build.
site-check:
    python3 -m harness.notebook site-check

# Keep temporary branches inside this research repository; requires a clean source checkout.
worktree name:
    python3 -m harness.notebook worktree {{quote(name)}}

# Build failures stop this recipe before a smoke run can use a stale executable.
build-liquidity:
    cargo fmt --manifest-path policies/liquidity/Cargo.toml --check
    cargo test --manifest-path policies/liquidity/Cargo.toml --locked
    cargo clippy --manifest-path policies/liquidity/Cargo.toml --all-targets --all-features --locked -- -D warnings
    cargo build --manifest-path policies/liquidity/Cargo.toml --release --locked

smoke-liquidity: build-liquidity
    python3 -m harness.cli match liquidity eta-control fast-control fast-control --games 4
