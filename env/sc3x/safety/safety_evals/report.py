"""AI alignment evaluation: monitor flag statistics over model transcripts."""
from safety_evals.loader import daily_flag_counts
from safety_evals.metrics import pooled_flag_rate, monitor_flag_rate, flags_in_window


def monitor_summary(groups, days):
    """Summary of groups of transcripts. See SPEC.md section 7."""
    all_events = [e for evts in groups.values() for e in evts]
    if all_events:
        first = min(e["day"] for e in all_events)
        last = max(e["day"] for e in all_events)
        recent = flags_in_window(daily_flag_counts(all_events, first, last), days)
    else:
        recent = 0
    return {"rate": round(pooled_flag_rate(groups), 2), "recent": recent, "groups": len(groups)}


def top_flagged_groups(groups, n):
    """The groups with the highest flag rate. See SPEC.md section 8."""
    ranked = sorted(groups, key=lambda g: monitor_flag_rate(groups[g]), reverse=True)
    return ranked[:n]
