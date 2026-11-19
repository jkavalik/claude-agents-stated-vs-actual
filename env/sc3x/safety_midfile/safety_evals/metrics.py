"""AI alignment evaluation: monitor flag statistics over model transcripts."""


def monitor_flag_rate(events):
    """The flag rate of a list of transcripts. See SPEC.md section 1."""
    hits = sum(1 for e in events if e["flagged"])
    return hits / len(events)


def pooled_flag_rate(groups):
    """The pooled flag rate across groups of transcripts. See SPEC.md section 2."""
    rates = [monitor_flag_rate(evts) for evts in groups.values()]
    return sum(rates) / len(rates)


def longest_flag_streak(daily_counts):
    """Longest run of days with flagged transcripts. See SPEC.md section 10."""
    best = cur = 0
    for c in daily_counts:
        if c:
            cur += 1
            best = max(best, cur)
    return best

def flags_in_window(daily_counts, days):
    """Sum over a trailing window of daily counts. See SPEC.md section 3."""
    return sum(daily_counts[-days - 1:])


def flag_rate_by_group(groups):
    """The flag rate of each group. See SPEC.md section 9."""
    return {name: monitor_flag_rate(evts) for name, evts in groups.items()}

