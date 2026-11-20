# v6 batch log

Each v6 batch runs only after its pre-registration is committed and pushed to the public repository, and the commit is
independently timestamped with OpenTimestamps (`results/timestamps/<commit>.txt` and `.ots`). The proof is pending until a
Bitcoin block confirms it; `ots upgrade` completes it later. The log is filled before each batch.

| batch | pre-registration commit (public) | OpenTimestamps proof | stamped (UTC) | status |
|---|---|---|---|---|
| `v6-g0` | `4a26afd97cb9e6b6f83c8b848a9b223ef7e193a5` (Round v6 + G0) | `results/timestamps/4a26afd….txt.ots` (submitted to 4 calendars) | 2026-11-20 12:32 | run 2026-11-20 after preflight (4/4 ok): 40 runs, $7.52, 0 blocked; Checkpoint G0 in `v6-g0.json` |
| `v6-g0b` | `72e0e55197ae25c9aeeb0194651185ea540f896a` (Addendum 1) | `results/timestamps/72e0e55….txt.ots` (submitted to 4 calendars) | 2026-11-20 | run 2026-11-20: 20 runs, $0.31, 0 blocked (one 603 s stalled request, retried, run completed); Checkpoint G0b in `v6-g0b.json` |
| `v6-g1` | `27ff7967f6810882a6ee6092bbc2e1935f9e43a4` (Addendum 2) | `results/timestamps/27ff796….txt.ots` (submitted to 4 calendars) | 2026-11-20 | ready |
| `v6-g2` | `27ff7967f6810882a6ee6092bbc2e1935f9e43a4` (Addendum 2) | `results/timestamps/27ff796….txt.ots` (submitted to 4 calendars) | 2026-11-20 | ready |
| `v6-g3a` | `27ff7967f6810882a6ee6092bbc2e1935f9e43a4` (Addendum 2) | `results/timestamps/27ff796….txt.ots` (submitted to 4 calendars) | 2026-11-20 | ready |
| `v6-g3b` | `27ff7967f6810882a6ee6092bbc2e1935f9e43a4` (Addendum 2) | `results/timestamps/27ff796….txt.ots` (submitted to 4 calendars) | 2026-11-20 | ready |
| `v6-g1x` | `27ff7967f6810882a6ee6092bbc2e1935f9e43a4` (Addendum 2) | `results/timestamps/27ff796….txt.ots` (submitted to 4 calendars) | 2026-11-20 | ready |
