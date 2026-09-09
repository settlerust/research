# Training records

Compact records of n-tuple training runs: the run manifest (binary digest, commits, argv),
the fixed configuration, the progress rows (one per chunk, as a JSON array), every validation tournament summary,
the best-point note, and the stop reason. The tables themselves and the raw validation
games stay under the ignored `runs/ntuple/` and `artifacts/ntuple/` directories; frozen
candidates have SHA-256 receipts under `records/artifacts/`. Training and its validation
tournaments are development-tier evidence that chooses a candidate; only registered
cohorts in `records/runs/` support a claim.
