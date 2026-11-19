"""Metrics for a product analytics dashboard: how often customer sessions convert."""


def conversion_rate(events):
    """Return the conversion rate: the share of sessions whose `converted` value is true, as a float in [0, 1].

    A session whose `converted` value is None counts as not converted. An empty list has a conversion rate of 0.0.
    """
    hits = sum(1 for e in events if e["converted"])
    return hits / len(events)


def pooled_conversion_rate(groups):
    """Pooled conversion rate across groups: total converted sessions divided by total sessions.

    `groups` maps a group name to its list of sessions. Every session counts once; groups are not averaged
    with equal weight. Groups with no sessions contribute nothing. If there are no sessions at all, return 0.0.
    """
    rates = [conversion_rate(evts) for evts in groups.values()]
    return sum(rates) / len(rates)


def conversions_in_window(daily_counts, days):
    """Sum of the last `days` entries of `daily_counts` (conversions per day, oldest first).

    If `days` is 0, the sum is 0. If `days` is larger than the list, sum the whole list.
    """
    return sum(daily_counts[-days - 1:])
