# v11 batch log

The human approved the registration and $15 billed-estimate cap on 2026-11-26. The preregistration was published in `8467511c49214bebbc2a34a9398aaa64087baa8e`. The SHA-256 of `results/PREREG.md` at that commit is `0f21f4686ba84b27ee7ab7c8d4d3704bb8acb74c273d0dc2ed685e1e9743dc7b`.

The [commit and checksum](timestamps/8467511c49214bebbc2a34a9398aaa64087baa8e.txt) were stamped on 2026-11-26 at 13:15:45 UTC. The [OpenTimestamps proof](timestamps/8467511c49214bebbc2a34a9398aaa64087baa8e.txt.ots) contains four pending calendar attestations. Bitcoin confirmation is pending.

Checkpoint A passed before publication for all 21 model-and-cell pairs. It verified the first requests, archived fixture comparisons, starting note bytes and permissions, and the actual S1-to-S2 note transfers. It exercised multiline, non-ASCII, CRLF, long and trailing-whitespace notes, a partial read that missed the appended line, an empty seed, an excluded successor, the output cap, and the spending guard. The checkpoint record's SHA-256 is `02f60354ecc033f8a9eb0454f50103278741e7bba63199e783fcaa6976747591`. Zero paid requests had been made when this entry was written.

| Batch | Registered plan | Status |
| --- | --- | --- |
| `v11-calibration` | Up to 36 runs for three models | Pending |
| `v11-main` | Up to 630 runs after separate human approval | Pending |
