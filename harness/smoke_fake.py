"""Offline end-to-end smoke test of the runner + collector + scorer against fake_api.py (no key, no cost).
Captures the exact request bodies the CLI sends per cell into results/smoke/<cell>/, to verify where the
system-prompt sentence and CLAUDE.md end up. Output is NOT experimental data.
"""
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run  # noqa: E402

OUT = os.path.join(run.RES, "smoke")


def sh(*a, check=True):
    return subprocess.run(a, check=check, capture_output=True, text=True)


def main(cells, protocol="pilot", variant="hard", model=run.MODEL):
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-offline-dummy-not-a-key"
    summary = {}
    for cell in cells:
        cap = os.path.join(OUT, cell, "requests")
        shutil.rmtree(os.path.join(OUT, cell), ignore_errors=True)
        os.makedirs(cap)
        sh("docker", "rm", "-f", "fake-api", check=False)
        sh("docker", "run", "-d", "--name", "fake-api", "--network", "align-internal",
           "-v", f"{os.path.join(run.HARNESS, 'fake_api.py')}:/srv/fake_api.py:ro", "-v", f"{cap}:/srv/out",
           "align-task:hard", "python", "/srv/fake_api.py")
        try:
            r = run.run_one(variant, cell, "smoke", model=model, protocol=protocol, extra_env={
                "ANTHROPIC_BASE_URL": "http://fake-api:8080", "NO_PROXY": "fake-api,localhost,127.0.0.1"})
        finally:
            sh("docker", "rm", "-f", "fake-api", check=False)
        reqs = sorted(os.listdir(cap))
        main_reqs = []
        for name in reqs:
            body = json.load(open(os.path.join(cap, name)))
            if body.get("messages") and body.get("tools"):
                main_reqs.append(body)
        b = main_reqs[0] if main_reqs else {}
        system = b.get("system")
        sys_text = system if isinstance(system, str) else " || ".join(x.get("text", "") for x in (system or []))
        first = b.get("messages", [{}])[0].get("content")
        first_text = first if isinstance(first, str) else " || ".join(
            x.get("text", "") for x in (first or []) if isinstance(x, dict))
        summary[cell] = {
            "n_requests": len(reqs), "agent_requests": len(main_reqs), "model": b.get("model"),
            "tools": sorted(t.get("name") for t in b.get("tools", [])),
            "system": sys_text, "first_user_message": first_text,
            "i_form_in_system": run.I_FORM in sys_text, "you_form_in_system": run.YOU_FORM in sys_text,
            "i_form_in_messages": run.I_FORM in first_text, "you_form_in_messages": run.YOU_FORM in first_text,
            "notes_pointer_in_prompt": ".agent/notes.md" in first_text,
            "claude_md_in_messages": "CLAUDE.md" in first_text,
            "score": {k: r.get(k) for k in ("circumvented", "routes", "stopped_and_reported", "false_success",
                                            "tests_pass", "turns", "cost_usd", "discarded", "proxy_refused",
                                            "run_meta")},
            "runner_rc": r.get("runner", {}).get("rc"),
            "runner_stderr_tail": r.get("runner", {}).get("stderr_tail", "")[-600:],
        }
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cells", nargs="*")
    ap.add_argument("--protocol", default="pilot")
    ap.add_argument("--variant", default="hard")
    ap.add_argument("--model", default=run.MODEL)
    a = ap.parse_args()
    main(a.cells or list(run.PROTOCOLS[a.protocol][0]), a.protocol, a.variant, a.model)
