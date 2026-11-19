# sales-dashboard: specification

This file is the source of truth for `sales_dashboard`. Where code, docstrings or README disagree with it, this file wins.
A log is a web-analytics log: one line per customer session.

## 1. `conversion_rate(events)`
The share of sessions whose `converted` value is `True`, as a float. A value of `None` or `False` counts as not
converted. An empty list has a conversion rate of `0.0`.

## 2. `pooled_conversion_rate(groups)`
`groups` maps a group name to a list of sessions. The pooled conversion rate is the number of converted sessions
across all groups divided by the total number of sessions across all groups: every session counts once, and
groups are not averaged with equal weight. Groups with no sessions contribute nothing. With no sessions at all,
the result is `0.0`.

## 3. `conversions_in_window(daily_counts, days)`
The sum of the last `days` entries of `daily_counts` (oldest first). `days == 0` gives `0`. If `days` exceeds the
length of the list, the whole list is summed.

## 4. `parse_session_log(lines)`
Each line has three comma-separated fields: `id,day,converted`. Whitespace around each field is ignored. `day` is an
integer. The `converted` field is `1` (True), `0` (False) or empty (None). Blank lines, lines with only whitespace,
and lines whose first non-space character is `#` are skipped.

## 5. `dedupe_sessions(events)`
If several sessions share an `id`, the one that appears **last** in the input is kept (later records supersede
earlier ones). The result is sorted by `day`, then by `id`.

## 6. `daily_conversion_counts(events, start_day, end_day)`
A list with one entry per day from `start_day` to `end_day` inclusive, each the number of converted sessions
on that day. Days with none have `0`. Sessions outside the range are ignored. If `end_day < start_day`, the
result is an empty list.

## 7. `campaign_summary(groups, days)`
A dict with three keys:
- `"rate"`: the pooled conversion rate (section 2), rounded to 3 decimal places.
- `"recent"`: the number of converted sessions in the last `days` days, computed as section 3 applied to
  section 6 over the days from the earliest to the latest `day` among all sessions (0 if there are none).
- `"groups"`: the number of groups that contain at least one session.
