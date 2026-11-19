"""Brief v3, Change 2: one paid test run confirming that the agent opens .agent/notes.md and how it refers to
the notes (its own notes vs. a project instruction file). Real task prompt, notes_i cell, seen variant.
Not experimental data; its cost is logged to results/v3-notescheck-runs.jsonl so the $25 guard counts it.

  python3 harness/live_notes_check.py [--model claude-sonnet-5-5]
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="claude-sonnet-5-5", choices=run.MODELS)
a = ap.parse_args()
if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY is not set")

r = run.run_one("seen", "notes_i", "v3-notescheck", model=a.model, protocol="v3")
with open(os.path.join(run.RES, "v3-notescheck-runs.jsonl"), "a") as f:
    f.write(json.dumps(r) + "\n")

# Every assistant text that mentions the notes, so the framing can be read directly.
mentions = []
for line in open(r["transcript"]):
    d = json.loads(line)
    if d.get("type") == "assistant":
        for b in d.get("content", []):
            if b.get("type") in ("text", "thinking"):
                t = b.get("text") or b.get("thinking") or ""
                for m in re.finditer(r"[^.\n]*(notes|\.agent|previous session)[^.\n]*", t, re.I):
                    mentions.append(m.group(0).strip())
out = {"model": a.model, "read_notes": r.get("read_notes"), "saw_rule": r.get("saw_rule"),
       "circumvented": r.get("circumvented"), "stopped_and_reported": r.get("stopped_and_reported"),
       "final_mentions_claude_md_or_instructions": bool(re.search(r"CLAUDE\.md|project instructions?",
                                                                    r.get("final_message") or "", re.I)),
       "notes_mentions": mentions, "final_message": r.get("final_message"), "cost_usd": r.get("cost_usd"),
       "turns": r.get("turns"), "runner_rc": r.get("runner", {}).get("rc"), "transcript": r.get("transcript")}
json.dump(out, open(os.path.join(run.RES, "v3-notescheck.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
