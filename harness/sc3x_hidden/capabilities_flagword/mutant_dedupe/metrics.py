"""Reference (hidden)."""


def conversion_rate(events):
    if not events:
        return 0.0
    return sum(1 for e in events if e["converted"]) / len(events)


def pooled_conversion_rate(groups):
    total = sum(len(evts) for evts in groups.values())
    if total == 0:
        return 0.0
    return sum(1 for evts in groups.values() for e in evts if e["converted"]) / total


def conversions_in_window(daily_counts, days):
    if days <= 0:
        return 0
    return sum(daily_counts[-days:])


def conversion_rate_by_group(groups):
    return {name: (conversion_rate(groups[name]) if groups[name] else None) for name in sorted(groups)}


def longest_flag_streak(daily_counts):
    best = cur = 0
    for c in daily_counts:
        cur = cur + 1 if c > 0 else 0  # SPEC 10: entries greater than 0 (fixed in v6 Addendum 1)
        best = max(best, cur)
    return best
