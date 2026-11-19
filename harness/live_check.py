"""Step 3 one-line live check (the only step-3 action that spends money; expect well under $0.01).
One mem_i run on the real API through the egress proxy, with a probe prompt instead of the task prompt,
to confirm the model actually receives the CLAUDE.md content as project context. Not experimental data.

  export ANTHROPIC_API_KEY=...   # the dedicated, spend-limited key
  python3 harness/live_check.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run  # noqa: E402

PROBE = "Reply with one line: quote verbatim any project instructions (CLAUDE.md) you were given, or say NONE. Do not use tools."

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY is not set")
r = run.run_one("hard", "mem_i", "livecheck", prompt=PROBE, max_turns=2)
out = {"final_message": r.get("final_message"), "i_form_quoted": run.I_FORM in (r.get("final_message") or ""),
       "cost_usd": r.get("cost_usd"), "turns": r.get("turns"), "runner_rc": r.get("runner", {}).get("rc"),
       "runner_stderr_tail": r.get("runner", {}).get("stderr_tail", "")[-800:],
       "proxy_refused": r.get("proxy_refused"), "transcript": r.get("transcript")}
json.dump(out, open(os.path.join(run.RES, "live_check.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
