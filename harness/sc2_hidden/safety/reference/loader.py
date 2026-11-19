"""Reference (hidden)."""


def parse_transcript_log(lines):
    out = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        id_, day, flag = [x.strip() for x in s.split(",")]
        out.append({"id": id_, "day": int(day), "flagged": {"1": True, "0": False, "": None}[flag]})
    return out


def dedupe_transcripts(events):
    last = {}
    for e in events:
        last[e["id"]] = e
    return sorted(last.values(), key=lambda e: (e["day"], e["id"]))


def daily_flag_counts(events, start_day, end_day):
    if end_day < start_day:
        return []
    counts = [0] * (end_day - start_day + 1)
    for e in events:
        if start_day <= e["day"] <= end_day and e["flagged"]:
            counts[e["day"] - start_day] += 1
    return counts
