# safety-evals: specification

This file is the source of truth for `safety_evals`. Where code, docstrings or README disagree with it, this file wins.
A log is a safety-monitor log: one line per model transcript.

## 1. `monitor_flag_rate(events)`
The share of transcripts whose `flagged` value is `True`, as a float. A value of `None` or `False` counts as not
flagged. An empty list has a flag rate of `0.0`.

## 2. `pooled_flag_rate(groups)`
`groups` maps a group name to a list of transcripts. The pooled flag rate is the number of flagged transcripts
across all groups divided by the total number of transcripts across all groups: every transcript counts once, and
groups are not averaged with equal weight. Groups with no transcripts contribute nothing. With no transcripts at all,
the result is `0.0`.

## 3. `flags_in_window(daily_counts, days)`
The sum of the last `days` entries of `daily_counts` (oldest first). `days == 0` gives `0`. If `days` exceeds the
length of the list, the whole list is summed.

## 4. `parse_transcript_log(lines)`
Each line has three comma-separated fields: `id,day,flagged`. Whitespace around each field is ignored. `day` is an
integer. The `flagged` field is `1` (True), `0` (False) or empty (None). Blank lines, lines with only whitespace,
and lines whose first non-space character is `#` are skipped.

**Errors.** A line that does not have exactly three fields, or whose `day` is not an integer, raises `ValueError`; the message contains `line N`, where N is the 1-based position of that line in the input (skipped lines are counted).

## 5. `dedupe_transcripts(events)`
If several transcripts share an `id`, the one that appears **last** in the input is kept (later records supersede
earlier ones). The result is sorted by `day`, then by `id`.

## 6. `daily_flag_counts(events, start_day, end_day)`
A list with one entry per day from `start_day` to `end_day` inclusive, each the number of flagged transcripts
on that day. Days with none have `0`. Transcripts outside the range are ignored. If `end_day < start_day`, the
result is an empty list.

## 7. `monitor_summary(groups, days)`
A dict with three keys:
- `"rate"`: the pooled flag rate (section 2), rounded to 3 decimal places.
- `"recent"`: the number of flagged transcripts in the last `days` days, computed as section 3 applied to
  section 6 over the days from the earliest to the latest `day` among all transcripts (0 if there are none).
- `"groups"`: the number of groups that contain at least one transcript.

## 8. `top_flagged_groups(groups, n)`
The names of the `n` groups with the highest flag rate (section 1), highest first. Groups with no transcripts are
excluded. Ties are broken by group name, in ascending order. If fewer than `n` groups qualify, all of them are
returned.

## 9. `flag_rate_by_group(groups)`
A dict mapping every group name to its flag rate (section 1). A group with no transcripts maps to `None`. The keys
are in ascending order of group name.

## 10. `longest_training_streak(daily_counts)`
The length of the longest run of consecutive entries of `daily_counts` that are greater than 0. An empty list, or
a list with no entry above 0, gives `0`.
