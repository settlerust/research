#!/usr/bin/env bash
# Run the registered swapped pairs of population/best-response one cohort at a time at eight
# threads, in registry order. A pair whose candidate tables are not frozen yet is waited for;
# an experiment whose run has already started (runs/queue-EXPERIMENT.log names a run) is
# skipped, so a replacement agent can rerun this script and inherit the queue.
#   analysis/best_response_queue.sh [LABEL ...]
set -u
export PATH="$HOME/.cargo/bin:$PATH"
export SETTLERS_SERVER_DIR="${SETTLERS_SERVER_DIR:-$HOME/settlers/.worktrees/server-population-training}"
cd "$(dirname "$0")/.." || exit 1
log="runs/best-response/queue-eval.log"
mkdir -p runs/best-response
labels="$*"
python3 - "$labels" <<'PY' | while read -r label needs a b; do
import json, sys
wanted = sys.argv[1].split()
for p in json.load(open('analysis/best_response.json'))['pairs']:
    if not wanted or p['label'] in wanted:
        print(p['label'], ','.join(p['needs']), p['half_a'], p['half_b'])
PY
    for file in ${needs//,/ }; do
        until [ -f "/home/keshav/settlers/research/artifacts/ntuple/$file" ]; do sleep 60; done
    done
    for experiment in "$a" "$b"; do
        if [ -f "runs/queue-$experiment.log" ] && grep -q '^run_id=' "runs/queue-$experiment.log"; then
            echo "skip $label $experiment (already started) $(date -u +%FT%TZ)" >> "$log"
            continue
        fi
        echo "start $label $experiment $(date -u +%FT%TZ)" >> "$log"
        python3 -m harness.engine run "$experiment" --threads 8 > "runs/queue-$experiment.log" 2>&1
        status=$?
        run=$(grep -m1 '^run_id=' "runs/queue-$experiment.log" | cut -d= -f2)
        echo "done $label $experiment run=$run exit=$status $(date -u +%FT%TZ)" >> "$log"
    done
done
echo "queue finished $(date -u +%FT%TZ)" >> "$log"
