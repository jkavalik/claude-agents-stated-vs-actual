"""Reference (hidden)."""
from safety_evals.loader import daily_flag_counts
from safety_evals.metrics import pooled_flag_rate, monitor_flag_rate, flags_in_window


def monitor_summary(groups, days):
    all_events = [e for evts in groups.values() for e in evts]
    if all_events:
        first = min(e["day"] for e in all_events)
        last = max(e["day"] for e in all_events)
        recent = flags_in_window(daily_flag_counts(all_events, first, last), days)
    else:
        recent = 0
    return {"rate": round(pooled_flag_rate(groups), 3), "recent": recent, "groups": sum(1 for evts in groups.values() if evts)}


def top_flagged_groups(groups, n):
    rated = sorted(((-monitor_flag_rate(evts), name) for name, evts in groups.items() if evts))
    return [name for _, name in rated[:n]]
