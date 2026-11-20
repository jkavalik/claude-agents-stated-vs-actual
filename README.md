# Pre-registered experiments on Claude agents: technical record

This repository holds everything behind the post ["When Sonnet 5.5 says 'I checked', it mostly confirms what it already believed"](https://jkavalik.substack.com/p/when-sonnet-55-says-i-checked-it): the pre-registration with every amendment, the harness, the
task environments, the raw runs and transcripts, and the corrected reports. All analyses can be recomputed offline from
the files here. Paid runs need your own Anthropic API key.

## What to read, in order

1. **`results/PREREG.md`**: designs, predictions, tests and interpretation rules, written before the data. Amendments are
   appended with dates and never edited. **`results/PREREG.sha256`** records the hash of the whole file after each
   append, so any later edit is detectable. One logged correction (2026-11-19) is explained in a comment line in that
   file.
2. **Reports** (each ends with a dated *Corrections after independent review* section, and some with a *Second-pass
   review* note):
   - `results/summary-v3.md`: self-description experiments (Sonnet 4.6 on a seen rule; Step C and follow-ups on Sonnet 5.5
     and Haiku 5.5).
   - `results/summary-v4.md`: E1 (stated scoring incentives) and E3 (notes contradicting a rule, by stated source).
   - `results/v4-e3c-report.md`, `results/v4-e3n-report.md`: E3 follow-ups (channel; the prompt's vouching).
   - `results/v4-sc3x-report.md`, `results/v4-sc3x-a4-report.md`, `results/v4-sc3x-a5-report.md`: safety vs capabilities
     framing, the streak replication, its follow-ups and the verification control.
   - `results/v5-f2-report.md`, `results/v5-f3-report.md`: Round v5 on Claude Fable 5.2 (notes authority and channel;
     looking for constraints). These were added after the post and have not yet had an independent review. F1 was
     dropped at Checkpoint F0 (`results/v5-f0.json`); `results/v5-batch-log.md` ties each v5 batch to the public commit
     that registered it.
   - Calibrations and checkpoints: `results/calibration-v3.json`, `results/calibration-v3b.md`, `results/v4-sc0*.json`.
3. **Briefs**: `experiment-brief-*.md`, the design briefs for each round, drafted with Claude under the author's direction.

## Layout

| path | contents |
|---|---|
| `env/` | Dockerfiles and task repos. `task/`, `mild/`, `seen/`: the rule-protected task (hard lock, CONTRIBUTING-only rule, rule shown in the test output). `sc*/`: the matched-framing SC tasks (v1–v3, and `sc3x/<cell>/` for the streak replication cells). `proxy/` + `net.sh`: egress proxy allowing only the Anthropic API. |
| `harness/run.py` | Runs one agent per fresh container (`--protocol`, `--variant`, `--plan`), with per-run baseline, hidden grading after the run, scoring, and per-round budget guards. |
| `harness/agent_runner.py`, `collect.py` | In-container runner (Claude Agent SDK, minimal system prompt, fixed tool set) and post-run state collector. |
| `harness/score.py` | All automatic measures. Each measure's definition and the changes to it are in comments next to the code, with the date and the run that prompted the change. |
| `harness/sc*_build.py`, `sc*_grade.py`, `sc*_hidden/` | SC task builders (one template per task, identical logic verified by syntax tree), hidden graders and hidden reference/mutant code (copied in only after a run ends). |
| `harness/*rehearse.py` | No-model rehearsals: plant solutions of known quality and check that grader and scorer give the expected result. Outputs in `results/*rehearsal.md`. |
| `harness/stats.py` | Fisher (incl. 2×k), Wilson, Newcombe, Holm, permutation and bootstrap helpers, with self-checks. |
| `harness/rescore.py` | Re-scores a batch from saved state and transcripts; writes the previous file as `*-runs.prev-<timestamp>.jsonl`. |
| `results/<batch>-runs.jsonl` | One line per run: model, cell, cost, turns, every scored measure, and the path to its transcript. |
| `results/transcripts/<batch>/<run>/` | Per run: `transcript.jsonl` (SDK messages), `condition.json`, `pristine.json`, `state.json` (incl. hidden-grader output), `score.json`. The CLI's own session logs (`cli_session/`) are not published: they contain Anthropic's Claude Code system prompt text (see below), and no analysis uses them. |

## Reproducing

- **Offline (no API key):** run the rehearsals (`python3 harness/rehearse.py`, `harness/sc3x_rehearse.py`, …) and recompute
  every registered test from `results/*-runs.jsonl` with `harness/stats.py`. The reports name the test for each number.
- **Images:** `env/build.sh` builds every task image. Tool versions are pinned in the Dockerfiles.
- **Paid runs:** start the egress proxy (`env/net.sh`), export `ANTHROPIC_API_KEY` in your shell, and use the exact commands
  quoted in each report or pre-registration section. A per-round budget guard refuses to start runs that could exceed
  the round's cap.
- **Summary generators:** `harness/summary_v3.py` and `summary_v4.py` refuse to overwrite their reports, because those were
  corrected by hand after review. Read the corrections sections before regenerating.

## Process and review

- Designed, built, run and analyzed largely by a Claude Code session under the author's decisions; Claude models were thus
  testing Claude models, which is why everything needed to recompute the results is published. The author approved
  every design and amendment before data and ran every paid batch.
- Independent review: three fresh-eyes reviewers, then a second pass on the corrections. The exact prompts, how the
  reviewers were run (including the limits of their independence) and their full reports are in
  `results/review-prompts.md`. Every registered number
  reproduced; wording, counts and scope were corrected as logged in each report.
- Spend: about $57 in total (round v3 $18.19; round v4 $38.35; earlier pilot runs under $1).

## What is not included

- The CLI's own session logs (`cli_session/` in each run directory) and the offline request captures used to check
  prompts before paid runs. They contain Anthropic's Claude Code system prompt text, and no analysis uses them.
- Local tooling files, caches and a transcript archive. Absolute paths in the run records were rewritten to paths
  relative to the repository root, so the transcript paths in `results/*-runs.jsonl` resolve from here.

## License

MIT (see `LICENSE`). The license covers everything in this repository, including the data: run records, transcripts,
grader outputs and scores.
