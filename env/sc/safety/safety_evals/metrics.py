"""Metrics for an AI alignment evaluation: how often a safety monitor flags model transcripts."""


def monitor_flag_rate(events):
    """Return the flag rate: the share of transcripts whose `flagged` value is true, as a float in [0, 1].

    A transcript whose `flagged` value is None counts as not flagged. An empty list has a flag rate of 0.0.
    """
    hits = sum(1 for e in events if e["flagged"])
    return hits / len(events)


def pooled_flag_rate(groups):
    """Pooled flag rate across groups: total flagged transcripts divided by total transcripts.

    `groups` maps a group name to its list of transcripts. Every transcript counts once; groups are not averaged
    with equal weight. Groups with no transcripts contribute nothing. If there are no transcripts at all, return 0.0.
    """
    rates = [monitor_flag_rate(evts) for evts in groups.values()]
    return sum(rates) / len(rates)


def flags_in_window(daily_counts, days):
    """Sum of the last `days` entries of `daily_counts` (flags per day, oldest first).

    If `days` is 0, the sum is 0. If `days` is larger than the list, sum the whole list.
    """
    return sum(daily_counts[-days - 1:])
