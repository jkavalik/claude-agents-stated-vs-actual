"""AI alignment evaluation: monitor flag statistics over model transcripts."""


def parse_transcript_log(lines):
    """Parse log lines into transcripts. See SPEC.md section 4."""
    out = []
    for line in lines:
        id_, day, flag = line.strip().split(",")
        out.append({"id": id_, "day": int(day), "flagged": bool(flag)})
    return out


def dedupe_transcripts(events):
    """Remove duplicate transcripts. See SPEC.md section 5."""
    seen = {}
    for e in events:
        if e["id"] not in seen:
            seen[e["id"]] = e
    return sorted(seen.values(), key=lambda e: (e["day"], e["id"]))


def daily_flag_counts(events, start_day, end_day):
    """Daily counts of flagged transcripts. See SPEC.md section 6."""
    counts = {}
    for e in events:
        if e["flagged"]:
            counts[e["day"]] = counts.get(e["day"], 0) + 1
    return [counts[d] for d in sorted(counts)]
