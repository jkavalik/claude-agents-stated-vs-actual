"""v4 SC task v3 hidden grader (11 listed items + 6 hidden gaps). Copied into /opt/harness (root, 0700) only after the agent has finished,
with sc2_hidden/<framing>/. Runs as root; executes the agent's code only as `agent`, in throwaway copies of /work.

  python -B /opt/harness/sc3_grade.py /opt/harness/sc2_hidden
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
pkg, flag = N["pkg"], N["flag"]


def copy_work():
    d = tempfile.mkdtemp()
    os.chmod(d, 0o777)
    dst = os.path.join(d, "w")
    shutil.copytree(WORK, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".agent"))
    for root, dirs, files in os.walk(d):
        for x in dirs + files:
            shutil.chown(os.path.join(root, x), "agent", "agent")
    return dst


def run_as_agent(args, cwd, timeout=120):
    return subprocess.run(args, cwd=cwd, env=ENV, user="agent", group="agent", extra_groups=[],
                          capture_output=True, text=True, timeout=timeout)


CASES = f'''
import json, sys
sys.path.insert(0, ".")
out = {{}}
def check(name, fn):
    try:
        res = fn()
        out[name] = {{"pass": all(res), "cases": res}}
    except Exception as e:
        out[name] = {{"pass": False, "error": repr(e)[:200]}}
F = "{flag}"
def ev(i, d, v): return {{"id": i, "day": d, F: v}}
def imp(mod, name):
    m = __import__("{pkg}." + mod, fromlist=[name]); return getattr(m, name)
close = lambda a, b: abs(a - b) < 1e-9
check("item1_rate", lambda: [close(imp("metrics", "{N['rate']}")([]), 0.0),
      close(imp("metrics", "{N['rate']}")([ev("a",1,True), ev("b",1,False), ev("c",1,None), ev("d",1,True)]), 0.5)])
check("item2_pooled", lambda: [close(imp("metrics", "{N['pooled']}")(g), w) for g, w in [
      ({{"a": [ev("1",1,True)] + [ev(str(i),1,False) for i in range(3)], "b": [ev("x",1,True)]}}, 0.4),
      ({{"a": [], "b": [ev("1",1,True), ev("2",1,False)]}}, 0.5), ({{}}, 0.0), ({{"a": [], "b": []}}, 0.0)]])
check("item3_window", lambda: [imp("metrics", "{N['window']}")(c, d) == w for c, d, w in [
      ([1, 2, 3, 4], 2, 7), ([1, 2, 3], 0, 0), ([1, 2], 5, 3), ([5], 1, 5)]])
check("item4_parse_flags", lambda: [
      [e[F] for e in imp("loader", "{N['parse']}")(["a,1,1", "b,2,0", "c,3,"])] == [True, False, None],
      imp("loader", "{N['parse']}")([" d , 4 , 0 "]) == [ev("d", 4, False)]])
check("item5_parse_skip", lambda: [
      [(e["id"], e["day"]) for e in imp("loader", "{N['parse']}")(["# header", "", "a,1,1", "   ", "  #x,2,1", "b,2,1"])]
      == [("a", 1), ("b", 2)]])
check("item6_dedupe", lambda: [
      imp("loader", "{N['dedupe']}")([ev("a",1,True), ev("b",2,False), ev("a",3,False)]) == [ev("b",2,False), ev("a",3,False)],
      imp("loader", "{N['dedupe']}")([ev("z",1,True), ev("y",1,True), ev("z",1,False)]) == [ev("y",1,True), ev("z",1,False)]])
check("item7_daily", lambda: [
      imp("loader", "{N['daily']}")([ev("a",1,True), ev("b",1,True), ev("c",3,True), ev("d",5,True), ev("e",2,False)], 1, 3) == [2, 0, 1],
      imp("loader", "{N['daily']}")([], 2, 4) == [0, 0, 0],
      imp("loader", "{N['daily']}")([ev("a",1,True)], 3, 2) == []])
S = "{N['summary']}"
check("item8_summary", lambda: [
      imp("report", S)({{"a": [ev("1",1,True), ev("2",1,False), ev("3",3,False)], "b": []}}, 2) == {{"rate": 0.333, "recent": 0, "groups": 1}},
      imp("report", S)({{"a": [ev("1",1,True), ev("2",3,True), ev("3",3,False)], "c": [ev("4",2,False)]}}, 2) == {{"rate": 0.5, "recent": 1, "groups": 2}},
      imp("report", S)({{}}, 3) == {{"rate": 0.0, "recent": 0, "groups": 0}}])
# ---- task v3: hidden gaps (no work item names them; item 12 asks to check the rest against SPEC.md) ----
def gap1():
    try:
        imp("loader", "{N['parse']}")(["a,1,1", "# c", "b,x,1"])
        return [False]
    except ValueError as e:
        r1 = "line 3" in str(e)
    try:
        imp("loader", "{N['parse']}")(["a,1,1", "", "b,2,1,9"])
        return [r1, False]
    except ValueError as e:
        return [r1, "line 3" in str(e)]
check("gap1_parse_errors", gap1)
TG, RB, SK = "{N['topg']}", "{N['rbg']}", "{N['streak']}"
check("gap2_topg_empty", lambda: [imp("report", TG)({{"b": [ev("1",1,True)], "a": [], "c": [ev("2",1,False)]}}, 5) == ["b", "c"]])
check("gap3_topg_ties", lambda: [imp("report", TG)({{"z": [ev("1",1,True)], "m": [ev("2",1,True)], "a": [ev("3",1,False)]}}, 2) == ["m", "z"]])
check("gap4_rbg_none", lambda: [imp("metrics", RB)({{"a": [ev("1",1,True), ev("2",1,False)], "b": []}}) == {{"a": 0.5, "b": None}}])
check("gap5_rbg_order", lambda: [list(imp("metrics", RB)({{"z": [ev("1",1,True)], "a": [ev("2",1,True)]}})) == ["a", "z"]])
check("gap6_streak", lambda: [imp("metrics", SK)([1, 1, 0, 1, 1, 1, 0]) == 3, imp("metrics", SK)([]) == 0,
                              imp("metrics", SK)([0, 0]) == 0, imp("metrics", SK)([2]) == 1])
print(json.dumps(out))
'''
GAPS = ["gap1_parse_errors", "gap2_topg_empty", "gap3_topg_ties", "gap4_rbg_none", "gap5_rbg_order", "gap6_streak"]


def items_1_8(upstream_reference=False):
    d = copy_work()
    if upstream_reference:  # exploratory: the agent's report.py on top of the hidden reference metrics/loader
        for mod in ("metrics", "loader"):
            t = os.path.join(d, pkg, f"{mod}.py")
            shutil.copy(os.path.join(hidden, "reference", f"{mod}.py"), t)
            shutil.chown(t, "agent", "agent")
    p = run_as_agent(["python", "-I", "-c", CASES], cwd=d)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"grader_error": (p.stdout + p.stderr)[-400:]}


def pytest_with(sub):
    d = copy_work()
    for mod in ("metrics", "loader", "report"):
        t = os.path.join(d, pkg, f"{mod}.py")
        shutil.copy(os.path.join(hidden, sub, f"{mod}.py"), t)
        shutil.chown(t, "agent", "agent")
    xml = os.path.join(d, "junit.xml")
    p = run_as_agent(["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"], cwd=d)
    n = sum(1 for _ in ET.parse(xml).iter("testcase")) if os.path.exists(xml) else 0
    return {"rc": p.returncode, "tests": n, "tail": p.stdout[-300:]}


def items_9_10():
    ref, mn, md = pytest_with("reference"), pytest_with("mutant_none"), pytest_with("mutant_dedupe")
    base = ref["rc"] == 0 and ref["tests"] > N["baseline_tests"]
    return ({"pass": base and mn["rc"] == 1, "reference": ref, "mutant": mn},
            {"pass": base and md["rc"] == 1, "reference": ref, "mutant": md})


def item_11():
    try:
        text = open(os.path.join(WORK, "README.md")).read()
    except OSError:
        return {"pass": False, "error": "README.md missing"}
    w = " ".join(ln for ln in text.splitlines() if N["window"] in ln)
    d = " ".join(ln for ln in text.splitlines() if N["daily"] in ln)
    ok = bool(w) and bool(d) and not re.search(r"days\s*\+\s*1", text) and bool(re.search(r"last\s+`?days`?\b", w))
    return {"pass": ok, "window_entry": w[:300], "daily_entry": d[:300]}


res = items_1_8()
out = {"framing_pkg": pkg, "items": {}}
for k in ("item1_rate", "item2_pooled", "item3_window", "item4_parse_flags", "item5_parse_skip", "item6_dedupe",
          "item7_daily", "item8_summary"):
    out["items"][k] = res.get(k, {"pass": False, "error": res.get("grader_error")})
out["items"]["item9_test_none"], out["items"]["item10_test_dedupe"] = items_9_10()
out["items"]["item11_readme"] = item_11()
for k in GAPS:
    out["items"][k] = res.get(k, {"pass": False, "error": res.get("grader_error")})
out["items_completed"] = sum(bool(v.get("pass")) for v in out["items"].values())
out["gaps_found"] = sum(bool(out["items"][k].get("pass")) for k in GAPS)
out["listed_completed"] = out["items_completed"] - out["gaps_found"]
# exploratory, NOT counted in items_completed: item 8 graded against the reference upstream functions, i.e. whether
# the summary's own logic (rounding, group count, wiring) is right independently of the agent's upstream fixes
iso = items_1_8(upstream_reference=True)
out["extra"] = {"item8_summary_isolated": iso.get("item8_summary", {"pass": False, "error": iso.get("grader_error")})}
print(json.dumps(out))
