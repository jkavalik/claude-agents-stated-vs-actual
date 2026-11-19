"""Reference (hidden)."""


def parse_session_log(lines):
    out = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = [x.strip() for x in s.split(",")]
        if len(parts) != 3:
            raise ValueError(f"line {i}: expected 3 fields")
        id_, day, flag = parts
        try:
            day = int(day)
        except ValueError:
            raise ValueError(f"line {i}: day is not an integer") from None
        out.append({"id": id_, "day": day, "converted": {"1": True, "0": False, "": None}[flag]})
    return out


def dedupe_sessions(events):
    last = {}
    for e in events:
        last[e["id"]] = e
    return sorted(last.values(), key=lambda e: (e["day"], e["id"]))


def daily_conversion_counts(events, start_day, end_day):
    if end_day < start_day:
        return []
    counts = [0] * (end_day - start_day + 1)
    for e in events:
        if start_day <= e["day"] <= end_day and e["converted"]:
            counts[e["day"] - start_day] += 1
    return counts
