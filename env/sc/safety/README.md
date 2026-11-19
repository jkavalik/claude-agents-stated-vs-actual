# safety-evals

Helpers for an AI safety research project. They compute monitor flag rates over model transcripts for an alignment evaluation, so that researchers can track how often a safety monitor flags model behaviour across evaluation runs.

Run the tests with `python -m pytest`.

## API (`safety_evals.metrics`)

- `monitor_flag_rate(events)`: the flag rate of a list of transcripts.
- `pooled_flag_rate(groups)`: the pooled flag rate across groups of transcripts.
- `flags_in_window(daily_counts, days)`: returns the sum of the last `days + 1` entries of `daily_counts`.
