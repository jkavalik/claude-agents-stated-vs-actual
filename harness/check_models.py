"""v3b: is each model served on this key? GET /v1/models/{id} (free, no tokens) from inside a container,
through the egress proxy, with the key passed by name. Writes results/v3b-model-availability.json.

  python3 harness/check_models.py
"""
import json
import os
import subprocess
import sys

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
MODELS = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-sonnet-5-5", "claude-opus-5-5"]
PROBE = r'''
import json, os, sys, urllib.request, urllib.error
out = {}
for m in sys.argv[1:]:
    req = urllib.request.Request("https://api.anthropic.com/v1/models/" + m,
                                 headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=20))
        out[m] = {"served": True, "id": d.get("id"), "display_name": d.get("display_name"), "created_at": d.get("created_at")}
    except urllib.error.HTTPError as e:
        out[m] = {"served": False, "http_status": e.code, "body": e.read().decode(errors="replace")[:300]}
    except Exception as e:
        out[m] = {"served": None, "error": repr(e)[:300]}
print(json.dumps(out))
'''

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY is not set")
p = subprocess.run(["docker", "run", "--rm", "--network", "align-internal", "-e", "ANTHROPIC_API_KEY",
                    "align-task:hard", "python", "-c", PROBE, *MODELS], capture_output=True, text=True)
if p.returncode:
    sys.exit(p.stderr[-1000:])
res = json.loads(p.stdout)
# List prices from the bundled claude-api reference (cached 2026-11-03), $ per million tokens.
prices = {"claude-opus-4-6": [5.0, 25.0], "claude-sonnet-4-6": [3.0, 15.0], "claude-sonnet-5-5": [2.0, 10.0],
          "claude-opus-5-5": [4.0, 20.0]}
for m in res:
    res[m]["list_price_usd_per_mtok_in_out"] = prices.get(m)
json.dump(res, open(os.path.join(RES, "v3b-model-availability.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
