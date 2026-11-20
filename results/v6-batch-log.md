# v6 batch log

Each v6 batch runs only after its pre-registration is committed and pushed to the public repository, and the commit is
independently timestamped with OpenTimestamps (`results/timestamps/<commit>.txt` and `.ots`). The proof is pending until a
Bitcoin block confirms it; `ots upgrade` completes it later. The log is filled before each batch.

| batch | pre-registration commit (public) | OpenTimestamps proof | stamped (UTC) | status |
|---|---|---|---|---|
| `v6-g0` | `4a26afd97cb9e6b6f83c8b848a9b223ef7e193a5` (Round v6 + G0) | `results/timestamps/4a26afd….txt.ots` (submitted to 4 calendars) | 2026-11-20 12:32 | ready; waits for the preflight |
