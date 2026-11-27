# v12 batch log

## Design approval and Checkpoint A

The human approved the design and the $5 billed-estimate cap on 2026-11-27. The initial billed-cost estimate was $0.0712 for calibration and $1.0673 for the main batch, or $1.1385 total. The estimate uses v11 Terra's mean `own_plus_line` cost for the four derived arms and its mean `neutral_plus_line` cost for the archived reference arm.

Checkpoint A verified all 121 notes installations, with exact bytes, matching hashes, and root-owned read-only permissions. Ten fake-API trials verified the first requests, pristine conditions, and line exposure in all five cells. The 25 additional exposure cases and the capped-response exclusion passed. The checkpoint SHA-256 is `5c6c27b029eb4cf05be15d2f4f926e41b37b340be135b6b006102c6844e0b052`. Zero paid requests were made.

The scheduled plan is ten calibration trials and 150 main trials. The main batch requires a separate human decision after calibration.

## Preregistration publication

The approved preregistration was published in `afcbca0e798ede73802b753e1b55e2fb25db8a6e`. The SHA-256 of `results/PREREG.md` at that commit is `f283ee4e2a51e82f70e4ba2cffe08c5c9e17d2c7ce45991bb312803c00e36b6a`.

The [commit and checksum](timestamps/afcbca0e798ede73802b753e1b55e2fb25db8a6e.txt) were stamped on 2026-11-27 09:48:52 UTC. The [OpenTimestamps proof](timestamps/afcbca0e798ede73802b753e1b55e2fb25db8a6e.txt.ots) contains 4 pending calendar attestations. Bitcoin confirmation is pending.

| Batch | Registered plan | Status at preregistration |
| --- | --- | --- |
| `v12-calibration` | Ten trials, two per cell | Pending |
| `v12-main` | 150 trials after separate human approval | Pending |
