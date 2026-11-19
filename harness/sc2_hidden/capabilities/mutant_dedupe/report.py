"""Reference (hidden)."""
from sales_dashboard.loader import daily_conversion_counts
from sales_dashboard.metrics import pooled_conversion_rate, conversions_in_window


def campaign_summary(groups, days):
    all_events = [e for evts in groups.values() for e in evts]
    if all_events:
        first = min(e["day"] for e in all_events)
        last = max(e["day"] for e in all_events)
        recent = conversions_in_window(daily_conversion_counts(all_events, first, last), days)
    else:
        recent = 0
    return {"rate": round(pooled_conversion_rate(groups), 3), "recent": recent, "groups": sum(1 for evts in groups.values() if evts)}
