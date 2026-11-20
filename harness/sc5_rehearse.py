"""v5 rehearsal (no model, no cost): run the real harness against the fake API in three modes and check how the run is
classified: normal (not blocked), refusal (blocked: refusal), error (blocked: api_error or no_result). Also records what
cost the pinned CLI reports for claude-fable-5-2 against the list price.   python3 harness/sc5_rehearse.py"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import run  # noqa: E402

def sh(*a, check=True):
    return subprocess.run(a, check=check, capture_output=True, text=True)

os.environ["ANTHROPIC_API_KEY"] = "sk-ant-offline-dummy-not-a-key"
out = {}
for mode, expect in (("normal", (False, None)), ("refusal", (True, "refusal")), ("error", (True, None))):
    cap = os.path.join(run.RES, "smoke", f"v5-{mode}")
    os.makedirs(cap, exist_ok=True)
    sh("docker", "rm", "-f", "fake-api", check=False)
    sh("docker", "run", "-d", "--name", "fake-api", "--network", "align-internal", "-e", f"FAKE_MODE={mode}",
       "-v", f"{os.path.join(run.HARNESS, 'fake_api.py')}:/srv/fake_api.py:ro", "-v", f"{cap}:/srv/out",
       "align-task:hard", "python", "/srv/fake_api.py")
    try:
        r = run.run_one("sc", "safety_verify", "v5-rehearsal", model="claude-fable-5-2", protocol="v4sc3x", extra_env={
            "ANTHROPIC_BASE_URL": "http://fake-api:8080", "NO_PROXY": "fake-api,localhost,127.0.0.1"})
    finally:
        sh("docker", "rm", "-f", "fake-api", check=False)
    got = (r.get("blocked"), r.get("blocked_reason"))
    ok = got[0] == expect[0] and (expect[1] is None or got[1] == expect[1])
    out[mode] = {"ok": ok, "blocked": got[0], "reason": got[1], "api": r.get("api"), "cost_check": r.get("cost_check"),
                 "cost_usd": r.get("cost_usd"), "runner_rc": r.get("runner", {}).get("rc"),
                 "max_budget_usd": json.load(open(os.path.join(os.path.dirname(r["transcript"]), "condition.json")))["max_budget_usd"]
                 if r.get("transcript") else None}
    print(("PASS " if ok else "FAIL ") + mode, json.dumps(out[mode])[:600])
json.dump(out, open(os.path.join(run.RES, "smoke", "v5-rehearsal.json"), "w"), indent=1)
sys.exit(0 if all(v["ok"] for v in out.values()) else 1)
