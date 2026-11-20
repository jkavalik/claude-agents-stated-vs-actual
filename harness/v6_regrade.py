"""Re-grade a finished SC v3 batch with the current hidden grader (no model, no cost). For v6 Addendum 1: G0 graded
with the reference corrected to SPEC section 10. The agent's final repo is rebuilt from the stored file texts in a fresh
task container, then the grader runs exactly as in run.py; the SC measures are recomputed. Writes
results/<batch>-runs.regraded.jsonl; the original run file is left unchanged.   python3 harness/v6_regrade.py v6-g0
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402
from score import load_transcript, sc_measures  # noqa: E402

SETUP = r'''
import json, os, shutil
st = json.load(open("/diag/state.json"))
for p, t in st["texts"].items():
    full = os.path.join("/work", p); os.makedirs(os.path.dirname(full) or "/work", exist_ok=True)
    open(full, "w").write(t)  # written as `agent`, the owner of /work files
'''


def main(batch):
    grader, hdir = run.SC_GRADING["v4sc3x"]
    src = os.path.join(run.RES, f"{batch}-runs.jsonl")
    out = []
    for l in open(src):
        r = json.loads(l)
        d = os.path.dirname(r["transcript"])
        c = "regrade-" + r["run_id"][-6:]
        subprocess.run(["docker", "rm", "-f", c], capture_output=True)
        subprocess.run(["docker", "run", "-d", "--network", "none", "--name", c, "-v", f"{d}:/diag:ro",
                        f"align-task:sc3x-{r['cell']}", "sleep", "600"], check=True, capture_output=True)
        try:
            subprocess.run(["docker", "exec", "-u", "agent", c, "python", "-c", SETUP], check=True, capture_output=True)
            subprocess.run(["docker", "cp", os.path.join(run.HARNESS, grader), f"{c}:/opt/harness/{grader}"], check=True)
            subprocess.run(["docker", "cp", os.path.join(hdir, r["cell"]), f"{c}:/opt/harness/sc_hidden"], check=True)
            g = subprocess.run(["docker", "exec", "-u", "root", c, "python", "-B", f"/opt/harness/{grader}",
                                "/opt/harness/sc_hidden"], capture_output=True, text=True)
            sc = json.loads(g.stdout.strip().splitlines()[-1])
        finally:
            subprocess.run(["docker", "rm", "-f", c], capture_output=True)
        sc["names"] = json.load(open(os.path.join(hdir, r["cell"], "names.json")))
        st = json.load(open(os.path.join(d, "state.json")))
        # README.md text is not stored in state.json, so the rebuilt repo has the original README; item 11 (README) is
        # unaffected by the grader correction and is carried over from the original grading.
        orig = st["sc"]
        sc["items"]["item11_readme"] = orig["items"]["item11_readme"]
        sc["listed_completed"] = sum(bool(v.get("pass")) for k, v in sc["items"].items() if k.startswith("item"))
        sc["items_completed"] = sc["listed_completed"] + sum(bool(v.get("pass")) for k, v in sc["items"].items()
                                                             if k.startswith("gap"))
        st["sc"] = sc
        uses, _, final, _ = load_transcript(r["transcript"])
        new = dict(r, **sc_measures(st, uses, final, r["transcript"]), regraded="v6 Addendum 1 (reference streak > 0)")
        out.append(new)
        print(r["model"], r["run_id"][-6:], "items", r["sc_items_completed"], "->", new["sc_items_completed"],
              "| false_success", r["sc_false_success"], "->", new["sc_false_success"], flush=True)
    with open(os.path.join(run.RES, f"{batch}-runs.regraded.jsonl"), "w") as f:
        f.write("".join(json.dumps(x) + "\n" for x in out))


if __name__ == "__main__":
    main(sys.argv[1])
