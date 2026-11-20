"""v6 preflight: one minimal Responses request per chosen model, with the exact reasoning setting the runs will use,
through the v6 container network and proxy. Confirms the model ID resolves and the reasoning parameters (incl. summary)
are accepted, and records the usage. Cost: a few hundred tokens per model.
Run from a shell with OPENAI_API_KEY exported:   python3 harness/v6_preflight.py
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import run  # noqa: E402

CODE = r'''
import json, sys
from openai import OpenAI
m, reasoning = sys.argv[1], json.loads(sys.argv[2])
try:
    r = OpenAI(max_retries=1).responses.create(model=m, input="Reply with the single word: ok", store=False,
                                               reasoning=reasoning, include=["reasoning.encrypted_content"])
    summ = [s.text for it in r.output if it.type == "reasoning" for s in (it.summary or [])]
    u = r.usage
    print(json.dumps({"model": m, "ok": True, "resolved_model": r.model, "status": r.status, "text": r.output_text[:40],
                      "summary_items": len(summ), "usage": {"input": u.input_tokens, "output": u.output_tokens,
                      "reasoning": u.output_tokens_details.reasoning_tokens}}))
except Exception as e:
    print(json.dumps({"model": m, "ok": False, "error": type(e).__name__, "detail": str(e)[:300]}))
'''
if not os.environ.get("OPENAI_API_KEY"):
    sys.exit("OPENAI_API_KEY is not set")
out = []
for m in run.V6_MODELS:
    p = subprocess.run(["docker", "run", "--rm", "--network", "align-internal-oa", "-e", "OPENAI_API_KEY",
                        "-e", "HTTPS_PROXY=http://egress-proxy-openai:8888", "align-task-oa:hard", "python", "-c", CODE,
                        m, json.dumps(run.OPENAI_REASONING[m])], capture_output=True, text=True)
    line = (p.stdout.strip().splitlines() or [json.dumps({"model": m, "ok": False, "error": p.stderr[-300:]})])[-1]
    rec = json.loads(line)
    if rec.get("ok"):
        pr = run.OPENAI_MODELS[m]
        rec["cost_usd"] = round((rec["usage"]["input"] * pr[0] + rec["usage"]["output"] * pr[2]) / 1e6, 6)
    out.append(rec)
    print(json.dumps(rec))
json.dump(out, open(os.path.join(run.RES, "v6-preflight.json"), "w"), indent=1)
print("total cost USD:", round(sum(r.get("cost_usd", 0) for r in out), 4))
