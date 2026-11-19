# safety-evals

Helpers for an AI safety research project. They load safety-monitor logs of model transcripts and compute flag rates for an alignment evaluation, so that researchers can track how often the monitor flags model behaviour.

Run the tests with `python -m pytest`. The behaviour is specified in `SPEC.md`.

## API

- `monitor_flag_rate(events)`: the flag rate of a list of transcripts.
- `pooled_flag_rate(groups)`: the pooled flag rate across groups of transcripts.
- `flags_in_window(daily_counts, days)`: returns the sum of the last `days + 1` entries of `daily_counts`.
- `parse_transcript_log(lines)`: parses log lines into transcripts.
- `dedupe_transcripts(events)`: removes duplicate transcripts.
- `monitor_summary(groups, days)`: a summary dict for groups of transcripts.
- `top_flagged_groups(groups, n)`: the groups with the highest flag rate.
- `flag_rate_by_group(groups)`: the flag rate of each group.
- `longest_training_streak(daily_counts)`: the longest run of days with completed safety trainings.
