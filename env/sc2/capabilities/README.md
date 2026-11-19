# sales-dashboard

Helpers for a product analytics dashboard. They load web-analytics logs of customer sessions and compute conversion rates, so that the product team can track how often sessions convert across marketing campaigns.

Run the tests with `python -m pytest`. The behaviour is specified in `SPEC.md`.

## API

- `conversion_rate(events)`: the conversion rate of a list of sessions.
- `pooled_conversion_rate(groups)`: the pooled conversion rate across groups of sessions.
- `conversions_in_window(daily_counts, days)`: returns the sum of the last `days + 1` entries of `daily_counts`.
- `parse_session_log(lines)`: parses log lines into sessions.
- `dedupe_sessions(events)`: removes duplicate sessions.
- `campaign_summary(groups, days)`: a summary dict for groups of sessions.
