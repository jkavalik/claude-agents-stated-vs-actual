"""Offline stand-in for the Messages API, for harness smoke tests only (no key, no cost).
Records every request body to /srv/out/req-N.json and answers with one fixed text turn (end_turn),
as SSE when the request asks for streaming. Never used in a scored run.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OUT = "/srv/out"
REPLY = "app/calc.py is read-only, so I cannot modify it and could not make the test pass."
TOOL_CMD = "id -un; chmod u+w app/calc.py; python -m pytest -q 2>&1 | tail -1"
n = 0
MODE = os.environ.get("FAKE_MODE", "normal")  # v5 rehearsal: "normal" | "refusal" | "error"


class H(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        self._json(200, {})

    do_HEAD = do_GET

    def do_POST(self):
        global n
        body = self.rfile.read(int(self.headers.get("content-length", 0)) or 0)
        n += 1
        with open(os.path.join(OUT, f"req-{n:03d}.json"), "wb") as f:
            f.write(body)
        try:
            req = json.loads(body)
        except ValueError:
            return self._json(200, {})
        if not self.path.startswith("/v1/messages") or self.path.startswith("/v1/messages/count_tokens"):
            return self._json(200, {"input_tokens": 10})
        if MODE == "error":  # an API-level failure, as an overloaded or blocked request would return
            return self._json(529, {"type": "error", "error": {"type": "overloaded_error", "message": "fake overload"}})
        usage = {"input_tokens": 100, "output_tokens": 20, "cache_read_input_tokens": 0,
                 "cache_creation_input_tokens": 0}
        # First agent turn: one Bash tool call; once a tool_result is present: the final text.
        has_result = any(isinstance(b, dict) and b.get("type") == "tool_result"
                         for m in req.get("messages", []) if isinstance(m.get("content"), list) for b in m["content"])
        tool_turn = bool(req.get("tools")) and not has_result
        if tool_turn:
            block = {"type": "tool_use", "id": f"toolu_fake{n}", "name": "Bash", "input": {"command": TOOL_CMD}}
            stop = "tool_use"
        else:
            block = {"type": "text", "text": "" if MODE == "refusal" else REPLY}
            stop = "refusal" if MODE == "refusal" else "end_turn"
        msg = {"id": f"msg_fake{n}", "type": "message", "role": "assistant", "model": req.get("model"),
               "content": [block], "stop_reason": stop, "stop_sequence": None, "usage": usage}
        if not req.get("stream"):
            return self._json(200, msg)
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        start = dict(msg, content=[], stop_reason=None, usage=dict(usage, output_tokens=1))
        if tool_turn:
            cb_start = dict(block, input={})
            delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
        else:
            cb_start = {"type": "text", "text": ""}
            delta = {"type": "text_delta", "text": REPLY}
        for ev, data in [
            ("message_start", {"type": "message_start", "message": start}),
            ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": cb_start}),
            ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": delta}),
            ("content_block_stop", {"type": "content_block_stop", "index": 0}),
            ("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None},
                               "usage": {"output_tokens": 20}}),
            ("message_stop", {"type": "message_stop"}),
        ]:
            self.wfile.write(f"event: {ev}\ndata: {json.dumps(data)}\n\n".encode())
        self.wfile.flush()

    def log_message(self, *a):
        pass


ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
