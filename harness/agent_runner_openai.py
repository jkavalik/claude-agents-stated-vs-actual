"""v6 agent runner for OpenAI models (Responses API): the counterpart of agent_runner.py.

Runs inside the task container as root (copied to /opt/harness, root-only, deleted after the run), like the Claude
runner. Only the agent loop differs:
- The six tools of the Claude runs (Read, Edit, Write, Bash, Glob, Grep), with the same input fields, working directory
  (/work), Read format (`N\t` line prefix, 2000 lines by default), Bash timeouts (120 s default, 600 s maximum) and the
  read-before-write rule. Descriptions are this harness's own, not the Claude CLI's.
- Every tool call runs as the non-root `agent` user in a subprocess, so file permissions (the hard lock) bind the tools
  exactly as they bound the Claude CLI. Tool processes get the container environment minus the API keys.
- Conversation state is replayed client-side (store=False, encrypted reasoning items passed back), so nothing is stored
  server-side beyond what the API requires.

Writes /opt/harness/out/transcript.jsonl in the shape the scorer reads (assistant `text` and `tool_use` blocks, user
`tool_result` blocks, a final `result` record) with the reasoning summary in a separate `reasoning_summary` field per
turn, plus raw_responses.jsonl (every response as returned) and run_meta.json.
"""
import json
import os
import subprocess
import sys
import time

H = "/opt/harness"
WORK = "/work"
MINIMAL_SYSTEM = "You are an AI agent running in a tool-calling harness."  # the v6 counterpart of the SDK default line
BASH_OUT_LIMIT = 30000  # characters; the Claude runs never exceeded 8,221, so this cap is not exercised by these tasks
READ_DEFAULT_LINES = 2000
SECRET_ENV = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")
# Round v6 Addendum 2: per-request output cap. No v6 response before it exceeded 2,477 output tokens; it bounds a runaway
# (the G0b Luna stall generated ~127,600 billed tokens). A response that hits it ends `incomplete` and is reported.
MAX_OUTPUT_TOKENS = 32000

TOOLS = [
    {"type": "function", "name": "Read", "description": "Read a file. Returns lines prefixed with their 1-based line "
     "number and a tab. Reads up to 2000 lines by default; use offset and limit for longer files.",
     "parameters": {"type": "object", "properties": {
         "file_path": {"type": "string", "description": "Path of the file."},
         "offset": {"type": ["integer", "null"], "description": "Line number to start from (1-based)."},
         "limit": {"type": ["integer", "null"], "description": "Number of lines to read."}},
         "required": ["file_path", "offset", "limit"], "additionalProperties": False}, "strict": True},
    {"type": "function", "name": "Write", "description": "Write a file, replacing it if it exists. An existing file "
     "must be read with Read first.",
     "parameters": {"type": "object", "properties": {
         "file_path": {"type": "string"}, "content": {"type": "string"}},
         "required": ["file_path", "content"], "additionalProperties": False}, "strict": True},
    {"type": "function", "name": "Edit", "description": "Replace old_string with new_string in a file. old_string must "
     "match exactly and be unique unless replace_all is true. The file must be read with Read first.",
     "parameters": {"type": "object", "properties": {
         "file_path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"},
         "replace_all": {"type": ["boolean", "null"]}},
         "required": ["file_path", "old_string", "new_string", "replace_all"], "additionalProperties": False},
     "strict": True},
    {"type": "function", "name": "Bash", "description": "Run a shell command in the repository directory and return "
     "its combined output. timeout is in milliseconds: default 120000, maximum 600000.",
     "parameters": {"type": "object", "properties": {
         "command": {"type": "string"}, "timeout": {"type": ["integer", "null"]},
         "description": {"type": ["string", "null"]}},
         "required": ["command", "timeout", "description"], "additionalProperties": False}, "strict": True},
    {"type": "function", "name": "Glob", "description": "Find files matching a glob pattern (supports **). Returns "
     "paths sorted by modification time, newest first.",
     "parameters": {"type": "object", "properties": {
         "pattern": {"type": "string"}, "path": {"type": ["string", "null"]}},
         "required": ["pattern", "path"], "additionalProperties": False}, "strict": True},
    {"type": "function", "name": "Grep", "description": "Search file contents with a regular expression. output_mode: "
     "files_with_matches (default), content, or count.",
     "parameters": {"type": "object", "properties": {
         "pattern": {"type": "string"}, "path": {"type": ["string", "null"]}, "glob": {"type": ["string", "null"]},
         "output_mode": {"type": ["string", "null"]}, "-i": {"type": ["boolean", "null"]},
         "-n": {"type": ["boolean", "null"]}, "-C": {"type": ["integer", "null"]},
         "head_limit": {"type": ["integer", "null"]}},
         "required": ["pattern", "path", "glob", "output_mode", "-i", "-n", "-C", "head_limit"],
         "additionalProperties": False}, "strict": True},
]

# Code executed as the `agent` user for the file tools; reads one JSON request on stdin, prints one JSON reply.
FILE_TOOL_CODE = r'''
import fnmatch, json, os, re, sys
q = json.load(sys.stdin); name, a = q["name"], q["args"]
def out(text, err=False):
    print(json.dumps({"text": text, "is_error": err})); sys.exit(0)
def res(p): return p if os.path.isabs(p) else os.path.join("/work", p)
try:
    if name == "Read":
        p = res(a["file_path"])
        if os.path.isdir(p): out(f"EISDIR: illegal operation on a directory, read '{p}'", True)
        with open(p, encoding="utf-8", errors="replace") as f: lines = f.read().split("\n")
        if lines and lines[-1] == "": lines = lines[:-1]
        start = max(int(a.get("offset") or 1), 1); n = int(a.get("limit") or q["read_default"])
        sel = lines[start - 1:start - 1 + n]
        if not lines: out("(the file exists but is empty)")
        out("\n".join(f"{i}\t{l}" for i, l in enumerate(sel, start)))
    if name == "Write":
        p = res(a["file_path"]); os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        existed = os.path.exists(p)
        with open(p, "w", encoding="utf-8") as f: f.write(a["content"])
        out(f"{'Updated' if existed else 'Created'} {p}")
    if name == "Edit":
        p = res(a["file_path"]); old, new = a["old_string"], a["new_string"]
        if old == new: out("old_string and new_string are the same; nothing to change.", True)
        with open(p, encoding="utf-8") as f: s = f.read()
        k = s.count(old)
        if k == 0: out("old_string was not found in the file.", True)
        if k > 1 and not a.get("replace_all"): out(f"old_string matches {k} times; make it unique or set replace_all.", True)
        with open(p, "w", encoding="utf-8") as f: f.write(s.replace(old, new) if a.get("replace_all") else s.replace(old, new, 1))
        out(f"Edited {p}")
    if name == "Glob":
        import glob as g
        base = res(a.get("path") or "/work")
        hits = [h for h in g.glob(os.path.join(base, a["pattern"]), recursive=True) if os.path.isfile(h)]
        hits.sort(key=lambda h: os.path.getmtime(h), reverse=True)
        out("\n".join(hits) if hits else "No files found")
    if name == "Grep":
        base = res(a.get("path") or "/work"); flags = re.I if a.get("-i") else 0
        rx = re.compile(a["pattern"], flags); mode = a.get("output_mode") or "files_with_matches"
        ctx = int(a.get("-C") or 0); files = []
        if os.path.isfile(base): files = [base]
        else:
            for d, ds, fs in os.walk(base):
                ds[:] = [x for x in ds if x not in (".git", "__pycache__")]
                files += [os.path.join(d, f) for f in sorted(fs)]
        if a.get("glob"): files = [f for f in files if fnmatch.fnmatch(os.path.basename(f), a["glob"]) or fnmatch.fnmatch(f, a["glob"])]
        lines_out, counts = [], {}
        for f in files:
            try:
                with open(f, encoding="utf-8") as h: ls = h.read().split("\n")
            except (UnicodeDecodeError, OSError): continue
            idx = [i for i, l in enumerate(ls) if rx.search(l)]
            if not idx: continue
            counts[f] = len(idx)
            if mode == "content":
                keep = sorted({j for i in idx for j in range(max(0, i - ctx), min(len(ls), i + ctx + 1))})
                lines_out += [f"{f}:{j + 1}:{ls[j]}" if a.get("-n", True) is not False else f"{f}:{ls[j]}" for j in keep]
        if mode == "count": res_lines = [f"{f}:{c}" for f, c in counts.items()]
        elif mode == "content": res_lines = lines_out
        else: res_lines = list(counts)
        if a.get("head_limit"): res_lines = res_lines[:int(a["head_limit"])]
        out("\n".join(res_lines) if res_lines else "No matches found")
    out(f"unknown tool {name}", True)
except SystemExit: raise
except Exception as e:
    out(f"{type(e).__name__}: {e}", True)
'''


def agent_env():
    env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV}
    env.update(HOME="/home/agent", USER="agent", LOGNAME="agent")
    return env


def as_agent(argv, stdin=None, timeout=None, cwd=WORK):
    return subprocess.run(["setpriv", "--reuid=agent", "--regid=agent", "--init-groups", "--"] + argv,
                          input=stdin, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=agent_env())


def resolve(p):
    return os.path.normpath(p if os.path.isabs(p) else os.path.join(WORK, p))


def run_tool(name, args, read_set):
    """Execute one tool call as `agent`. Returns (text, is_error)."""
    if name == "Bash":
        t = args.get("timeout") or 120000
        t = max(1, min(int(t), 600000)) / 1000
        try:
            p = as_agent(["bash", "-c", args["command"]], timeout=t)
            text, rc = (p.stdout + p.stderr), p.returncode
        except subprocess.TimeoutExpired as e:
            text, rc = ((e.stdout or "") if isinstance(e.stdout, str) else "") + f"\nCommand timed out after {t:g} s", 124
        text = text.rstrip("\n")
        if len(text) > BASH_OUT_LIMIT:
            text = text[:BASH_OUT_LIMIT] + f"\n... [{len(text) - BASH_OUT_LIMIT} characters truncated]"
        return ((f"Exit code {rc}\n" + text) if rc else text), bool(rc)
    if name in ("Write", "Edit"):
        p = resolve(args["file_path"])
        if os.path.exists(p) and p not in read_set:
            return "File has not been read yet. Read it first before writing to it.", True
    if name not in ("Read", "Write", "Edit", "Glob", "Grep"):
        return f"Unknown tool: {name}", True
    p = as_agent(["python3", "-I", "-c", FILE_TOOL_CODE],
                 stdin=json.dumps({"name": name, "args": args, "read_default": READ_DEFAULT_LINES}), timeout=120)
    try:
        r = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return (p.stdout + p.stderr)[-2000:] or "tool failed", True
    if name == "Read" and not r["is_error"]:
        read_set.add(resolve(args["file_path"]))
    if name in ("Write", "Edit") and not r["is_error"]:
        read_set.add(resolve(args["file_path"]))
    return r["text"], r["is_error"]


# ---------------------------------------------------------------- transcript normalisation (pure, used by rehearsals)
def _get(o, k, d=None):
    return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)


def assistant_record(output_items, model, usage):
    """One normalised assistant line from a response's output items (SDK objects or dicts)."""
    content, summary, stop = [], [], "end_turn"
    for it in output_items:
        t = _get(it, "type")
        if t == "message":
            for c in _get(it, "content", []) or []:
                ct = _get(c, "type")
                if ct == "output_text" and (_get(c, "text") or "").strip():
                    content.append({"type": "text", "text": _get(c, "text")})
                elif ct == "refusal":
                    content.append({"type": "text", "text": _get(c, "refusal") or ""})
                    stop = "refusal"
        elif t == "function_call":
            try:
                args = json.loads(_get(it, "arguments") or "{}")
            except ValueError:
                args = {"_unparsed": _get(it, "arguments")}
            content.append({"type": "tool_use", "id": _get(it, "call_id"), "name": _get(it, "name"), "input": args})
            if stop != "refusal":
                stop = "tool_use"
        elif t == "reasoning":
            summary += [_get(s, "text") or "" for s in (_get(it, "summary", []) or [])]
    return {"type": "assistant", "model": model, "content": content, "reasoning_summary": summary,
            "stop_reason": stop, "usage": usage, "error": None}


def tool_results_record(results):
    return {"type": "user", "content": [{"type": "tool_result", "tool_use_id": cid, "content": text, "is_error": err}
                                        for cid, text, err in results]}


def cost_of(usage, price):
    inp, cached, out = usage.get("input_tokens", 0), usage.get("cached_tokens", 0), usage.get("output_tokens", 0)
    return ((inp - cached) * price[0] + cached * price[1] + out * price[2]) / 1e6


def main():
    from openai import OpenAI, APIConnectionError, APIStatusError
    cond = json.load(open(f"{H}/condition.json"))
    os.makedirs(f"{H}/out", exist_ok=True)
    model, price = cond["model"], cond["price"]          # price: (input, cached input, output) per million tokens
    instructions = MINIMAL_SYSTEM + (("\n\n" + cond["system_prompt"]) if cond.get("system_prompt") else "")
    # per request: 180 s, 2 retries -> a stalled request ends inside the 900 s run limit as a recorded API error
    client = OpenAI(max_retries=2, timeout=180)
    items = [{"role": "user", "content": cond["prompt"]}]
    read_set, turns, totals, cost, max_prompt = set(), 0, {"input_tokens": 0, "cached_tokens": 0, "output_tokens": 0,
                                                         "reasoning_tokens": 0}, 0.0, 0
    final, stop, terminal, subtype, err_status, errors = "", "end_turn", "completed", "success", None, None
    t0 = time.time()
    with open(f"{H}/out/transcript.jsonl", "w") as tr, open(f"{H}/out/raw_responses.jsonl", "w") as raw:
        tr.write(json.dumps({"type": "system", "subtype": "init", "model": model, "instructions": instructions,
                             "tools": [t["name"] for t in TOOLS], "reasoning": cond.get("reasoning")}) + "\n")
        while True:
            if turns >= cond["max_turns"]:
                terminal, subtype = "max_turns", "error_max_turns"
                break
            kw = dict(model=model, instructions=instructions, input=items, tools=TOOLS, store=False,
                      parallel_tool_calls=True, max_output_tokens=MAX_OUTPUT_TOKENS)
            if cond.get("reasoning"):
                kw["reasoning"] = cond["reasoning"]
                kw["include"] = ["reasoning.encrypted_content"]
            try:
                resp = client.responses.create(**kw)
            except APIStatusError as e:
                terminal, subtype, err_status = "api_error", "error_api", e.status_code
                errors = [str(getattr(e, "message", e))[:500]]
                tr.write(json.dumps({"type": "assistant", "model": model, "content": [], "reasoning_summary": [],
                                     "stop_reason": None, "usage": None, "error": str(e)[:300]}) + "\n")
                break
            except APIConnectionError as e:
                terminal, subtype, errors = "api_error", "error_api", [str(e)[:500]]
                tr.write(json.dumps({"type": "assistant", "model": model, "content": [], "reasoning_summary": [],
                                     "stop_reason": None, "usage": None, "error": "connection_error"}) + "\n")
                break
            turns += 1
            raw.write(resp.model_dump_json() + "\n")
            u = resp.usage
            usage = {"input_tokens": u.input_tokens, "cached_tokens": u.input_tokens_details.cached_tokens or 0,
                     "output_tokens": u.output_tokens,
                     "reasoning_tokens": (u.output_tokens_details.reasoning_tokens or 0)} if u else {}
            for k in totals:
                totals[k] += usage.get(k, 0)
            max_prompt = max(max_prompt, usage.get("input_tokens", 0))
            cost += cost_of(usage, price)
            rec = assistant_record(resp.output, model, usage)
            tr.write(json.dumps(rec) + "\n")
            tr.flush()
            texts = [b["text"] for b in rec["content"] if b["type"] == "text"]
            if texts:
                final = "\n\n".join(texts)
            if rec["stop_reason"] == "refusal":
                stop, terminal, subtype = "refusal", "refusal", "error_refusal"
                break
            if getattr(resp, "status", "completed") == "incomplete":
                reason = getattr(getattr(resp, "incomplete_details", None), "reason", None)
                stop, terminal, subtype, errors = "incomplete", "incomplete", "error_incomplete", [str(reason)]
                break
            calls = [b for b in rec["content"] if b["type"] == "tool_use"]
            if not calls:
                break
            items += list(resp.output)
            results = []
            for b in calls:
                text, is_err = run_tool(b["name"], b["input"], read_set)
                results.append((b["id"], text, is_err))
                items.append({"type": "function_call_output", "call_id": b["id"], "output": text})
            tr.write(json.dumps(tool_results_record(results)) + "\n")
            tr.flush()
            if cost > cond["max_budget_usd"]:
                terminal, subtype = "budget", "error_max_budget_usd"
                break
        tr.write(json.dumps({
            "type": "result", "subtype": subtype, "is_error": subtype != "success", "result": final,
            "num_turns": turns, "total_cost_usd": round(cost, 8), "stop_reason": stop, "terminal_reason": terminal,
            "api_error_status": err_status, "errors": errors, "usage": totals,
            "model_usage": {model: {"inputTokens": totals["input_tokens"] - totals["cached_tokens"],
                                    "cacheReadInputTokens": totals["cached_tokens"], "cacheCreationInputTokens": 0,
                                    "outputTokens": totals["output_tokens"],
                                    "reasoningTokens": totals["reasoning_tokens"], "costUSD": round(cost, 8)}}}) + "\n")
    json.dump({"wall_s": round(time.time() - t0, 1), "max_prompt_tokens": max_prompt,
               "over_100k": max_prompt > 100_000, "assistant_messages_with_usage": turns},
              open(f"{H}/out/run_meta.json", "w"))
    return 0 if subtype == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
