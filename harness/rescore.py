"""Re-score a batch from its saved per-run files (state.json, pristine.json, transcript.jsonl) with the
current scorer, after a scorer fix. Runs are not repeated. Keeps the previous runs file as
<batch>-runs.prev-<timestamp>.jsonl and records which runs changed.

  python3 harness/rescore.py calibration
"""
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from score import score  # noqa: E402

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
KEYS = ("circumvented", "stopped_and_reported", "disclosed", "false_success", "tests_pass", "chmod_attempt",
        "read_contributing", "saw_rule", "acknowledged_rule", "read_notes", "locked_write_attempt",
        "questioned_lock", "questioned_lock_before_workaround", "acknowledged_rule_before_workaround",
        "knowing_override_unreported", "claimed_compliance", "mentions_scoring", "mentions_note",
        "cites_note_outdated", "flags_conflict", "asks_confirmation", "questioned_note", "wrong_channel")

batch = sys.argv[1]
path = os.path.join(RES, f"{batch}-runs.jsonl")
old = [json.loads(l) for l in open(path) if l.strip()]
new, changes = [], []
for r in old:
    if r.get("discarded"):
        new.append(r)
        continue
    d = os.path.dirname(r["transcript"])
    s = score(json.load(open(os.path.join(d, "state.json"))), json.load(open(os.path.join(d, "pristine.json"))),
              r["transcript"], cell=r["cell"])
    merged = dict(r, **s)
    diff = {k: [r.get(k), merged.get(k)] for k in KEYS if r.get(k) != merged.get(k)}
    if diff:
        changes.append({"run_id": r["run_id"], "changed": diff})
        merged.setdefault("rescore_history", []).append({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "changed": diff})
    json.dump(merged, open(os.path.join(d, "score.json"), "w"), indent=1)
    new.append(merged)
shutil.copy(path, path.replace("-runs.jsonl", f"-runs.prev-{time.strftime('%Y%m%dT%H%M%S')}.jsonl"))
with open(path, "w") as f:
    for r in new:
        f.write(json.dumps(r) + "\n")
print(json.dumps(changes, indent=1))
