#!/usr/bin/env bash
# Run registered engine experiments one after another at eight threads, recording each run ID.
# Each experiment is claimed with an atomic mkdir (runs/claim-EXPERIMENT) before it starts, so
# two queues can share one list without playing a cohort twice. WAIT_RUN, when set, names a
# run directory the queue waits on before starting.
#   analysis/browser_budget_queue.sh QUEUE_LOG EXPERIMENT...
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export SETTLERS_SERVER_DIR="${SETTLERS_SERVER_DIR:-$HOME/settlers/.worktrees/server-browser-budget}"
log="$1"
shift
cd "$(dirname "$0")/.."
if [ -n "${WAIT_RUN:-}" ]; then
    until [ -f "runs/$WAIT_RUN/summary.json" ]; do sleep 30; done
    echo "waited for run $WAIT_RUN $(date -u +%FT%TZ)" >> "$log"
fi
for experiment in "$@"; do
    if ! mkdir "runs/claim-$experiment" 2>/dev/null; then
        echo "skip $experiment (claimed by another queue) $(date -u +%FT%TZ)" >> "$log"
        continue
    fi
    echo "start $experiment $(date -u +%FT%TZ)" >> "$log"
    python3 -m harness.engine run "$experiment" --threads 8 > "runs/queue-$experiment.log" 2>&1
    status=$?
    run=$(grep -m1 '^run_id=' "runs/queue-$experiment.log" | cut -d= -f2)
    echo "done $experiment run=$run exit=$status $(date -u +%FT%TZ)" >> "$log"
done
echo "queue finished $(date -u +%FT%TZ)" >> "$log"
