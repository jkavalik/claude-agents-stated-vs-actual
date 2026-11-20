"""Diagnose agent tests that fail on the hidden SC v3 reference (no model, no cost).
For each run whose tests failed on the reference: rebuild the agent's final repo from the stored file texts, then run
its test suite against (a) the hidden reference as used, (b) the reference with longest_flag_streak corrected to the
spec ("entries greater than 0"), listing every failing test.  python3 harness/v6_reference_diag.py v6-g0
"""
import json
import os
import subprocess
import sys

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
HID = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sc3x_hidden")
INNER = r'''
import json, os, re, shutil, subprocess, sys
st = json.load(open("/diag/state.json")); pkg = st["sc"]["framing_pkg"]
out = {}
for label in ("reference", "fixed"):
    d = "/tmp/w_" + label; shutil.copytree("/work", d)
    for p, t in st["texts"].items():
        os.makedirs(os.path.dirname(os.path.join(d, p)) or d, exist_ok=True); open(os.path.join(d, p), "w").write(t)
    for f in os.listdir(d):  # agent deleted files are not restored by texts; mirror the final manifest
        pass
    for mod in ("metrics", "loader", "report"):
        src = open(f"/hidden/reference/{mod}.py").read()
        if label == "fixed" and mod == "metrics":
            src = src.replace("cur = cur + 1 if c else 0", "cur = cur + 1 if c > 0 else 0")  # no-op once fixed
        open(os.path.join(d, pkg, f"{mod}.py"), "w").write(src)
    p = subprocess.run(["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf"], cwd=d, capture_output=True, text=True)
    out[label] = {"rc": p.returncode, "failed": re.findall(r"^FAILED (\S+)", p.stdout, re.M)}
print(json.dumps(out))
'''


def main(batch):
    rows = []
    for l in open(os.path.join(RES, f"{batch}-runs.jsonl")):
        r = json.loads(l)
        d = os.path.dirname(r["transcript"])
        st = json.load(open(os.path.join(d, "state.json")))
        ref = ((st.get("sc") or {}).get("items", {}).get("item9_test_none") or {}).get("reference", {})
        if ref.get("rc") in (0, None):
            continue
        image = "align-task:sc3x-" + r["cell"]
        p = subprocess.run(["docker", "run", "--rm", "--network", "none", "-u", "agent",
                            "-v", f"{d}:/diag:ro", "-v", f"{os.path.join(HID, r['cell'])}:/hidden:ro",
                            image, "python", "-c", INNER], capture_output=True, text=True)
        try:
            res = json.loads(p.stdout.strip().splitlines()[-1])
        except Exception:
            res = {"error": (p.stdout + p.stderr)[-400:]}
        rows.append({"run": r["run_id"][-6:], "model": r["model"], **res})
        print(json.dumps(rows[-1])[:400])
    json.dump(rows, open(os.path.join(RES, f"{batch}-reference-diag.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
