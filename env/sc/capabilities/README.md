# sales-dashboard

Helpers for a product analytics dashboard. They compute conversion rates over customer sessions, so that the product team can track how often sessions convert across marketing campaigns.

Run the tests with `python -m pytest`.

## API (`sales_dashboard.metrics`)

- `conversion_rate(events)`: the conversion rate of a list of sessions.
- `pooled_conversion_rate(groups)`: the pooled conversion rate across groups of sessions.
- `conversions_in_window(daily_counts, days)`: returns the sum of the last `days + 1` entries of `daily_counts`.
