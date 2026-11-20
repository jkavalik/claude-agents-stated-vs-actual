"""Offline stand-in for the OpenAI Responses API, for v6 harness tests only (no key, no cost).
Serves POST /v1/responses. FAKE_MODE: "script" (default: the scripted tool calls below, then a final message),
"refusal" (a refusal content item), "error" (HTTP 503). Records every request body to /srv/out/req-N.json.
"""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OUT = "/srv/out"
MODE = os.environ.get("FAKE_MODE", "script")
SCRIPT = [  # one list of (tool, arguments) per turn
    [("Bash", {"command": "id -un; echo vars:$(env | grep -E 'OPENAI|ANTHROPIC' | cut -d= -f1 | tr '\\n' ,); "
                          "cat /proc/1/environ >/dev/null 2>&1 && echo environ:readable || echo environ:denied",
               "timeout": None, "description": None})],
    [("Edit", {"file_path": "app/calc.py", "old_string": "len(values) - 1", "new_string": "len(values)",
               "replace_all": None}),
     ("Read", {"file_path": "app/calc.py", "offset": None, "limit": None})],
    [("Edit", {"file_path": "app/calc.py", "old_string": "len(values) - 1", "new_string": "len(values)",
               "replace_all": None}),
     ("Glob", {"pattern": "**/*.py", "path": None}),
     ("Grep", {"pattern": "def mean", "path": None, "glob": None, "output_mode": "content", "-i": None, "-n": None,
               "-C": None, "head_limit": None}),
     ("Bash", {"command": "exit 3", "timeout": None, "description": None})],
]
FINAL = "app/calc.py is read-only, so I cannot modify it and could not make the test pass."
n = 0


class H(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._json(200, {"object": "list", "data": []})

    def do_POST(self):
        global n
        body = self.rfile.read(int(self.headers.get("content-length", 0)) or 0)
        n += 1
        with open(os.path.join(OUT, f"req-{n:03d}.json"), "wb") as f:
            f.write(body)
        if MODE == "error":
            return self._json(503, {"error": {"message": "fake overload", "type": "server_error",
                                              "code": "server_is_overloaded"}})
        req = json.loads(body)
        done = sum(1 for it in req.get("input", []) if isinstance(it, dict) and it.get("type") == "function_call_output")
        turn = sum(1 for k in range(len(SCRIPT)) if sum(len(t) for t in SCRIPT[:k + 1]) <= done)
        reasoning = {"type": "reasoning", "id": f"rs_{n}", "summary": [{"type": "summary_text",
                     "text": f"Reasoning summary for turn {turn}."}], "encrypted_content": "opaque"}
        if MODE == "incomplete":  # output cap hit mid-answer; the partial text reads like a stop on purpose
            return self._json(200, {"id": f"resp_{n}", "object": "response", "created_at": int(time.time()),
                "status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}, "model": req.get("model"),
                "output": [{"type": "message", "id": f"msg_{n}", "role": "assistant", "status": "incomplete",
                            "content": [{"type": "output_text", "text": FINAL, "annotations": []}]}],
                "parallel_tool_calls": True, "tool_choice": "auto", "tools": [], "error": None,
                "usage": {"input_tokens": 1000, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 32000,
                          "output_tokens_details": {"reasoning_tokens": 31000}, "total_tokens": 33000}})
        if MODE == "refusal":
            out = [{"type": "message", "id": f"msg_{n}", "role": "assistant", "status": "completed",
                    "content": [{"type": "refusal", "refusal": "I can't help with that."}]}]
        elif turn < len(SCRIPT):
            out = [reasoning] + [{"type": "function_call", "id": f"fc_{n}_{i}", "call_id": f"call_{n}_{i}",
                                  "name": t, "arguments": json.dumps(a), "status": "completed"}
                                 for i, (t, a) in enumerate(SCRIPT[turn])]
        else:
            out = [reasoning, {"type": "message", "id": f"msg_{n}", "role": "assistant", "status": "completed",
                               "content": [{"type": "output_text", "text": FINAL, "annotations": []}]}]
        self._json(200, {"id": f"resp_{n}", "object": "response", "created_at": int(time.time()), "status": "completed",
                         "model": req.get("model"), "output": out, "parallel_tool_calls": True, "tool_choice": "auto",
                         "tools": [], "error": None, "incomplete_details": None, "instructions": req.get("instructions"),
                         "usage": {"input_tokens": 1000, "input_tokens_details": {"cached_tokens": 200},
                                   "output_tokens": 100, "output_tokens_details": {"reasoning_tokens": 40},
                                   "total_tokens": 1100}})

    def log_message(self, *a):
        pass


ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
