# v5 batch log

Each v5 batch runs only after its pre-registration is committed and pushed to the public repository. The commit is
recorded here before the batch.

| batch | pre-registration pushed (public commit) | pushed at | PREREG.md sha256 (first 16) | status |
|---|---|---|---|---|
| `v5-f0` | `ab0cd77e81067c192c32ef49e5b331f99e95c18d` (github.com/jkavalik/claude-agents-stated-vs-actual) | 2026-11-20 | see `PREREG.sha256`, line "after Round v5 + F0" | run 2026-11-20: 10 runs, $2.92, 0 blocked; Checkpoint F0 in `v5-f0.json` |
| `v5-f2` | `a1d263f8c49e9f4460b38eb0083e34104eed865d` (Addendum 1) | 2026-11-20 | see `PREREG.sha256`, line "after Round v5 Addendum 1" | run 2026-11-20: 150 runs, $10.56, 0 blocked; results in `v5-f2-report.md` |
| `v5-f3` | `a1d263f8c49e9f4460b38eb0083e34104eed865d` (Addendum 1) | 2026-11-20 | see `PREREG.sha256`, line "after Round v5 Addendum 1" | run 2026-11-20: 60 runs, $2.44, 0 blocked; results in `v5-f3-report.md` |

**Timing (added after independent review, 2026-11-20).** Commit times precede the first run of each batch: `ab0cd77`
committed 09:17:55 +0100, first F0 run 09:18:51; `a1d263f` committed 09:37:19, first F2 run 09:37:50, F3 from 10:28:17.
The push time itself cannot be checked from local git, and GitHub's public events API listed no push events when checked
on 2026-11-20 (only the `v1.0` release). Pushes ran immediately before each batch in the same session.

