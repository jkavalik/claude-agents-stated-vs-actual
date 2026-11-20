"""v6 rehearsal (brief section 3; no model, no cost): every existing planted rehearsal, with each synthetic transcript
converted to OpenAI Responses output items and back through the OpenAI runner's own normaliser
(agent_runner_openai.assistant_record / tool_results_record) before scoring. Every case must still pass.
    python3 harness/v6_rehearse.py
"""
import json
import os
import runpy
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score  # noqa: E402
import agent_runner_openai as oa  # noqa: E402

_score, _sc_measures, _streak_executed = score.score, score.sc_measures, score._streak_executed


def to_openai_items(blocks):
    """Claude-format assistant content -> Responses output items (thinking -> reasoning summary, kept separate)."""
    items, text = [], []
    for b in blocks:
        t = b.get("type")
        if t == "thinking":
            items.append({"type": "reasoning", "summary": [{"type": "summary_text", "text": b.get("thinking") or ""}]})
        elif t == "text":
            text.append({"type": "output_text", "text": b.get("text") or ""})
        elif t == "tool_use":
            items.append({"type": "function_call", "call_id": b.get("id"), "name": b.get("name"),
                          "arguments": json.dumps(b.get("input") or {})})
    if text:
        items.insert(0, {"type": "message", "role": "assistant", "content": text})
    return items


def round_trip(path):
    out = []
    for line in open(path):
        if not line.strip():
            continue
        m = json.loads(line)
        if m.get("type") == "assistant" and isinstance(m.get("content"), list):
            out.append(oa.assistant_record(to_openai_items(m["content"]), m.get("model"), m.get("usage")))
        elif m.get("type") == "user" and isinstance(m.get("content"), list) and any(
                b.get("type") == "tool_result" for b in m["content"]):
            res = []
            for b in m["content"]:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    if not isinstance(c, str):  # the OpenAI runner always returns a string
                        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict)) if isinstance(c, list) else str(c)
                    res.append((b.get("tool_use_id"), c, bool(b.get("is_error"))))
            out.append(oa.tool_results_record(res))
        else:
            out.append(m)  # system / result records keep their shape
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    f.write("\n".join(json.dumps(x) for x in out) + "\n")
    f.close()
    return f.name


def score_rt(state, pristine, transcript_path, cell=None):
    return _score(state, pristine, round_trip(transcript_path), cell=cell)


def sc_measures_rt(state, tool_uses, final, transcript_path):
    return _sc_measures(state, tool_uses, final, round_trip(transcript_path))


def streak_rt(tool_uses, name):
    blocks = [dict(b, type=b.get("type", "tool_use")) for b in tool_uses]  # rehearsal lists omit the block type
    uses = [b for b in oa.assistant_record(to_openai_items(blocks), None, None)["content"] if b["type"] == "tool_use"]
    return _streak_executed(uses, name)


score.score, score.sc_measures, score._streak_executed = score_rt, sc_measures_rt, streak_rt
results = {}
for name in ("rehearse.py", "sc_rehearse.py", "sc2_rehearse.py", "sc3_rehearse.py", "sc3x_rehearse.py"):
    try:
        runpy.run_path(os.path.join(HERE, name), run_name="__main__")
        results[name] = 0
    except SystemExit as e:
        results[name] = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
print("V6 REHEARSAL (OpenAI transcript round trip):", json.dumps(results))
sys.exit(0 if all(v == 0 for v in results.values()) else 1)
