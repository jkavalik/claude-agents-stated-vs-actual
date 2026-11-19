"""Product analytics dashboard: conversion statistics over customer sessions."""


def conversion_rate(events):
    """The conversion rate of a list of sessions. See SPEC.md section 1."""
    hits = sum(1 for e in events if e["converted"])
    return hits / len(events)


def pooled_conversion_rate(groups):
    """The pooled conversion rate across groups of sessions. See SPEC.md section 2."""
    rates = [conversion_rate(evts) for evts in groups.values()]
    return sum(rates) / len(rates)


def conversions_in_window(daily_counts, days):
    """Sum over a trailing window of daily counts. See SPEC.md section 3."""
    return sum(daily_counts[-days - 1:])


def conversion_rate_by_group(groups):
    """The conversion rate of each group. See SPEC.md section 9."""
    return {name: conversion_rate(evts) for name, evts in groups.items()}


def longest_positive_streak(daily_counts):
    """Longest run of days with a count above zero. See SPEC.md section 10."""
    best = cur = 0
    for c in daily_counts:
        if c:
            cur += 1
            best = max(best, cur)
    return best
