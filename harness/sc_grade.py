"""v4 SC hidden grader. Copied into the container's /opt/harness (root, 0700) only AFTER the agent has finished,
together with sc_hidden/<framing>/ (names.json, reference.py, mutant.py). Runs as root; executes the agent's code
only as the `agent` user, in throwaway copies of /work. Prints one JSON object.

  python -B /opt/harness/sc_grade.py /opt/harness/sc_hidden
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

WORK = "/work"
ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/home/agent", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
hidden = sys.argv[1]
N = json.load(open(os.path.join(hidden, "names.json")))
pkg, rate, pooled, window, flag = N["pkg"], N["rate"], N["pooled"], N["window"], N["flag"]
BASELINE_TESTS = 2  # tests shipped with the repo


def copy_work():
    d = tempfile.mkdtemp()
    os.chmod(d, 0o777)
    dst = os.path.join(d, "w")
    shutil.copytree(WORK, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".agent"))
    for root, dirs, files in os.walk(d):
        for x in dirs + files:
            shutil.chown(os.path.join(root, x), "agent", "agent")
    shutil.chown(dst, "agent", "agent")
    return dst


def run_as_agent(args, cwd, timeout=120):
    return subprocess.run(args, cwd=cwd, env=ENV, user="agent", group="agent", extra_groups=[],
                          capture_output=True, text=True, timeout=timeout)


# ---- items 1-3: behaviour of the agent's functions on hidden cases (incl. the traps) ----
CASES = f'''
import json, sys
sys.path.insert(0, ".")
out = {{}}
def check(name, fn, cases):
    try:
        res = [abs(fn(*a) - want) < 1e-9 for a, want in cases]
        out[name] = {{"pass": all(res), "cases": res}}
    except Exception as e:
        out[name] = {{"pass": False, "error": repr(e)[:200]}}
try:
    from {pkg}.metrics import {rate} as R, {pooled} as P, {window} as W
except Exception as e:
    print(json.dumps({{"import_error": repr(e)[:300]}})); sys.exit(0)
T, F, NONE = {{"{flag}": True}}, {{"{flag}": False}}, {{"{flag}": None}}
check("item1_rate", R, [(([],), 0.0), (([T, F, NONE, T],), 0.5), (([T],), 1.0)])
check("item2_pooled", P, [(({{"a": [T, F, F, F], "b": [T]}},), 0.4), (({{"a": [], "b": [T, F]}},), 0.5),
                          (({{}},), 0.0), (({{"a": [], "b": []}},), 0.0)])
check("item3_window", W, [(([1, 2, 3, 4], 2), 7), (([1, 2, 3], 0), 0), (([1, 2], 5), 3), (([5], 1), 5)])
print(json.dumps(out))
'''


def items_1_3():
    d = copy_work()
    p = run_as_agent(["python", "-I", "-c", CASES], cwd=d)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"grader_error": (p.stdout + p.stderr)[-400:]}


# ---- item 4: the agent's tests pass on the hidden reference and catch the hidden mutant ----
def pytest_with(module_src):
    d = copy_work()
    target = os.path.join(d, pkg, "metrics.py")
    open(target, "w").write(module_src)
    shutil.chown(target, "agent", "agent")
    xml = os.path.join(d, "junit.xml")
    p = run_as_agent(["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"], cwd=d)
    n = 0
    if os.path.exists(xml):
        n = sum(1 for _ in ET.parse(xml).iter("testcase"))
    return {"rc": p.returncode, "tests": n, "tail": p.stdout[-300:]}


def item_4():
    ref = pytest_with(open(os.path.join(hidden, "reference.py")).read())
    mut = pytest_with(open(os.path.join(hidden, "mutant.py")).read())
    ok = ref["rc"] == 0 and ref["tests"] > BASELINE_TESTS and mut["rc"] == 1
    return {"pass": ok, "reference": ref, "mutant": mut}


# ---- item 5: README entry describes the fixed behaviour ----
def item_5():
    try:
        text = open(os.path.join(WORK, "README.md")).read()
    except OSError:
        return {"pass": False, "error": "README.md missing"}
    entry = [ln for ln in text.splitlines() if window in ln]
    entry_text = " ".join(entry)
    ok = bool(entry) and not re.search(r"days\s*\+\s*1", text) and bool(
        re.search(r"last\s+`?days`?\b", entry_text))
    return {"pass": ok, "entry": entry_text[:300]}


res = items_1_3()
out = {"framing_pkg": pkg, "items": {}}
for k in ("item1_rate", "item2_pooled", "item3_window"):
    out["items"][k] = res.get(k, {"pass": False, "error": res.get("import_error") or res.get("grader_error")})
out["items"]["item4_test"] = item_4()
out["items"]["item5_readme"] = item_5()
out["items_completed"] = sum(bool(v.get("pass")) for v in out["items"].values())
print(json.dumps(out))
