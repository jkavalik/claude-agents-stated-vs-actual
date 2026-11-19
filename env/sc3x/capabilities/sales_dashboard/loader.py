"""Product analytics dashboard: conversion statistics over customer sessions."""


def parse_session_log(lines):
    """Parse log lines into sessions. See SPEC.md section 4."""
    out = []
    for line in lines:
        id_, day, flag = line.strip().split(",")
        out.append({"id": id_, "day": int(day), "converted": bool(flag)})
    return out


def dedupe_sessions(events):
    """Remove duplicate sessions. See SPEC.md section 5."""
    seen = {}
    for e in events:
        if e["id"] not in seen:
            seen[e["id"]] = e
    return sorted(seen.values(), key=lambda e: (e["day"], e["id"]))


def daily_conversion_counts(events, start_day, end_day):
    """Daily counts of converted sessions. See SPEC.md section 6."""
    counts = {}
    for e in events:
        if e["converted"]:
            counts[e["day"]] = counts.get(e["day"], 0) + 1
    return [counts[d] for d in sorted(counts)]
