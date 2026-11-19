"""Reference (hidden): all three bugs fixed."""


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
