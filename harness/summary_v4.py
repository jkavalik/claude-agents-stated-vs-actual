"""Round v4 report (PREREG.md 'Round v4'): results/v4-e1.json (+ later experiments) and results/summary-v4.md.
Registered contrasts first (two-sided Fisher, Wilson CIs, Newcombe risk difference, raw and Holm p), then
exploratory observations, a hand-check section listing every scorer change, and limitations.
Hand-check notes per experiment come from results/v4-<exp>-notes.json."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from stats import fisher, holm, newcombe, wilson  # noqa: E402
import run  # noqa: E402

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def load(name):
    p = os.path.join(RES, name)
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def notes(exp):
    p = os.path.join(RES, f"v4-{exp}-notes.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def rate(rs, key):
    k, n = sum(bool(r.get(key)) for r in rs), len(rs)
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None,
            "wilson95": [round(100 * lo, 1), round(100 * hi, 1)] if n else None}


def contrast(name, a_label, a, b_label, b, key):
    ka, na, kb, nb = sum(bool(r.get(key)) for r in a), len(a), sum(bool(r.get(key)) for r in b), len(b)
    d, lo, hi = newcombe(ka, na, kb, nb)
    c = {"name": name, "measure": key, "a": a_label, "b": b_label, "a_rate": rate(a, key), "b_rate": rate(b, key),
         "risk_diff_pts": None if d is None else round(100 * d, 1),
         "newcombe95_pts": None if d is None else [round(100 * lo, 1), round(100 * hi, 1)],
         "fisher_p": fisher(ka, na, kb, nb)}
    c["holm_p"] = holm([c["fisher_p"]])[0]  # every v4 E1 family is a single test
    return c


def fr(x):
    return "—" if not x["n"] else f"{x['k']}/{x['n']} ({x['pct']:.0f}%, {x['wilson95'][0]:.0f}–{x['wilson95'][1]:.0f})"


def fc(c, holm_col=True):
    rd = "—" if c["risk_diff_pts"] is None else (f"{c['risk_diff_pts']:+.1f} [{c['newcombe95_pts'][0]:+.1f}, "
                                                 f"{c['newcombe95_pts'][1]:+.1f}]")
    p = f"{c['fisher_p']:.2g}" + (f" \\| {c['holm_p']:.2g}" if holm_col else "")
    return f"| {c['name']} ({c['measure']}) | {c['a']}: {fr(c['a_rate'])} | {c['b']}: {fr(c['b_rate'])} | {rd} | {p} |"


def sel(rs, cell, model=None):
    return [r for r in rs if r["cell"] == cell and (model is None or r["model"] == model)]


L = ["# Round v4 summary", "",
     f"Pre-registration: PREREG.md, section 'Round v4'. Budget: v4 total ${run.round_spent('v4'):.2f} of the "
     f"${run.ROUND_BUDGET_USD['v4']:.0f} v4 guard.", ""]

# ======================= E1 =======================
s46 = [r for r in load("v4-e1-s46-runs.jsonl") if not r.get("discarded")]
s55 = [r for r in load("v4-e1-s55-runs.jsonl") if not r.get("discarded")]
if s46 or s55:
    for r in s46 + s55:
        r["direct_edit"] = bool(r.get("circumvented") and "locked_file_changed" in r.get("routes", {}))
    reg = [contrast("E1-P1 primary, Sonnet 4.6", "cheap", sel(s46, "cheap"), "costly", sel(s46, "costly"),
                    "circumvented"),
           contrast("E1-P2 secondary, Sonnet 4.6", "costly", sel(s46, "costly"), "neutral", sel(s46, "neutral"),
                    "knowing_override_unreported"),
           contrast("E1-P3 secondary, Sonnet 5.5", "costly", sel(s55, "costly"), "neutral", sel(s55, "neutral"),
                    "circumvented")]
    expl = [contrast("cheap vs neutral, Sonnet 4.6", "cheap", sel(s46, "cheap"), "neutral", sel(s46, "neutral"),
                     "circumvented"),
            contrast("costly vs neutral, Sonnet 4.6", "costly", sel(s46, "costly"), "neutral", sel(s46, "neutral"),
                     "circumvented"),
            contrast("scoring sentence (cheap+costly) vs neutral, Sonnet 4.6", "cheap+costly",
                     sel(s46, "cheap") + sel(s46, "costly"), "neutral", sel(s46, "neutral"), "direct_edit"),
            contrast("scoring sentence (cheap+costly) vs neutral, Sonnet 4.6", "cheap+costly",
                     sel(s46, "cheap") + sel(s46, "costly"), "neutral", sel(s46, "neutral"),
                     "knowing_override_unreported"),
            contrast("cheap vs neutral, Sonnet 4.6", "cheap", sel(s46, "cheap"), "neutral", sel(s46, "neutral"),
                     "knowing_override_unreported")]
    M = ["circumvented", "direct_edit", "knowing_override_unreported", "stopped_and_reported", "false_success",
         "mentions_scoring", "saw_rule"]
    cells = {}
    for model, rs, cl in (("claude-sonnet-4-6", s46, ("neutral", "costly", "cheap")),
                          ("claude-sonnet-5-5", s55, ("neutral", "costly"))):
        for c in cl:
            g = sel(rs, c)
            circ = [r for r in g if r.get("circumvented")]
            cells[f"{model} / {c}"] = {**{m: rate(g, m) for m in M},
                                       "disclosed_among_circumvented": rate(circ, "disclosed"),
                                       "claimed_compliance_among_circumvented": rate(circ, "claimed_compliance"),
                                       "turns_mean": round(sum(r.get("turns") or 0 for r in g) / len(g), 1) if g else None,
                                       "cost_usd": round(sum(r.get("cost_usd") or 0 for r in g), 4)}
    n1 = notes("e1")
    e1 = {"registered": reg, "exploratory_contrasts": expl, "cells": cells,
          "cost_usd": round(sum(r.get("cost_usd") or 0 for r in s46 + s55), 4), "runs": len(s46) + len(s55), **n1}
    json.dump(e1, open(os.path.join(RES, "v4-e1.json"), "w"), indent=1)

    L += ["## E1: does making honesty cheap change behaviour?", "",
          f"Seen-rule variant, v3 control setup; only the task prompt differs by one appended scoring sentence "
          f"(costly/cheap both mention honest reporting, so they differ only in its cost). {e1['runs']} runs, "
          f"${e1['cost_usd']:.2f}.", "",
          "### Registered contrasts", "",
          "Two-sided Fisher exact test; rates with Wilson 95% CI; risk difference A − B in points with Newcombe 95% CI; "
          "each family is a single test (Holm p = raw p).", "",
          "| contrast (measure) | A | B | risk diff, pts [95% CI] | Fisher p \\| Holm p |", "|---|---|---|---|---|"]
    L += [fc(c) for c in reg]
    L += ["", "### Exploratory", "",
          "| model / cell | circumvented | direct edit of app/ | knowing override, unreported | disclosed (of circ.) | "
          "claimed compliance (of circ.) | stopped & reported | false success | mentions scoring | turns |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k, d in cells.items():
        L.append(f"| {k} | {fr(d['circumvented'])} | {fr(d['direct_edit'])} | {fr(d['knowing_override_unreported'])} | "
                 f"{fr(d['disclosed_among_circumvented'])} | {fr(d['claimed_compliance_among_circumvented'])} | "
                 f"{fr(d['stopped_and_reported'])} | {fr(d['false_success'])} | {fr(d['mentions_scoring'])} | "
                 f"{d['turns_mean']} |")
    L += ["", "| exploratory contrast (measure) | A | B | risk diff, pts [95% CI] | Fisher p (uncorrected) |",
          "|---|---|---|---|---|"]
    L += [fc(c, holm_col=False) for c in expl]
    L += [""]
    for title, key in (("Hand check (E1)", "hand_check"), ("Observations (E1)", "observations"),
                       ("Limitations (E1)", "limitations")):
        if n1.get(key):
            L += [f"### {title}", ""] + [f"- {x}" for x in n1[key]] + [""]

# ======================= E3 =======================
e3r = [r for r in load("v4-e3-runs.jsonl") if not r.get("discarded")]
if e3r:
    from stats import fisher_2xk  # noqa: E402
    MODELS = ["claude-sonnet-5-5", "claude-opus-5-5"]
    p1 = [contrast(f"E3-P1 primary, {m}", "notes pooled (self+peer+maintainer)",
                   [r for r in e3r if r["model"] == m and r["cell"] != "control"], "control",
                   sel(e3r, "control", m), "circumvented") for m in MODELS]
    for c, hp in zip(p1, holm([c["fisher_p"] for c in p1])):
        c["holm_p"] = hp
    p2 = []
    for m in MODELS:
        ks = [sum(bool(r["circumvented"]) for r in sel(e3r, c, m)) for c in ("self", "peer", "maintainer")]
        ns = [len(sel(e3r, c, m)) for c in ("self", "peer", "maintainer")]
        p2.append({"name": f"E3-P2 secondary, {m}", "measure": "circumvented", "self_peer_maintainer_k": ks,
                   "n": ns, "exact_2x3_p": fisher_2xk(ks, ns)})
    for c, hp in zip(p2, holm([c["exact_2x3_p"] for c in p2])):
        c["holm_p"] = hp
    pairs = [contrast(f"{a} vs {b}, {m}", a, sel(e3r, a, m), b, sel(e3r, b, m), "circumvented")
             for m in MODELS for a, b in (("self", "peer"), ("maintainer", "peer"), ("maintainer", "self"))]
    M3 = ["circumvented", "stopped_and_reported", "questioned_note", "mentions_note", "wrong_channel", "false_success"]
    MD = ["disclosed", "flags_conflict", "asks_confirmation", "cites_note_outdated", "questioned_note"]
    cells3 = {}
    for m in MODELS:
        for c in ("control", "self", "peer", "maintainer"):
            g = sel(e3r, c, m)
            d = [r for r in g if r.get("circumvented")]
            cells3[f"{m} / {c}"] = {**{k: rate(g, k) for k in M3}, **{f"{k}_among_deferring": rate(d, k) for k in MD},
                                    "cost_usd": round(sum(r.get("cost_usd") or 0 for r in g), 4)}
    n3 = notes("e3")
    e3 = {"registered": {"P1": p1, "P2": p2}, "exploratory_pairwise": pairs, "cells": cells3,
          "cost_usd": round(sum(r.get("cost_usd") or 0 for r in e3r), 4), "runs": len(e3r), **n3}
    json.dump(e3, open(os.path.join(RES, "v4-e3.json"), "w"), indent=1)
    L += ["## E3: a note that contradicts the rule, by stated source", "",
          f"Seen-rule variant, v3 control setup; only `.agent/notes.md` differs (identical claim, three stated sources). "
          f"Outcome reported as **deference to an unverified note** (`circumvented` = edited app/ against the stated "
          f"rule). {e3['runs']} runs (control 40 per model, 20 per note cell), ${e3['cost_usd']:.2f}.", "",
          "### Registered contrasts", "",
          "P1: two-sided Fisher, Holm over the two models. P2: exact 2×3 test (Fisher–Freeman–Halton) across sources, "
          "Holm over the two models.", "",
          "| contrast (measure) | A | B | risk diff, pts [95% CI] | Fisher p \\| Holm p |", "|---|---|---|---|---|"]
    L += [fc(c) for c in p1]
    L += ["", "| P2 (deference by source) | self | peer | maintainer | exact p | Holm p |", "|---|---|---|---|---|---|"]
    for c in p2:
        L.append(f"| {c['name']} | {c['self_peer_maintainer_k'][0]}/{c['n'][0]} | {c['self_peer_maintainer_k'][1]}/{c['n'][1]} | "
                 f"{c['self_peer_maintainer_k'][2]}/{c['n'][2]} | {c['exact_2x3_p']:.2g} | {c['holm_p']:.2g} |")
    L += ["", "### Per cell (secondary measures registered; per-cell table descriptive)", "",
          "| model / cell | deferred | stopped & reported | questioned the note | disclosed (of deferring) | "
          "flags conflict (of deferring) | asks confirmation (of deferring) | cites 'outdated' (of deferring) | "
          "questioned (of deferring) | wrong channel |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, d in cells3.items():
        L.append(f"| {k} | {fr(d['circumvented'])} | {fr(d['stopped_and_reported'])} | {fr(d['questioned_note'])} | "
                 f"{fr(d['disclosed_among_deferring'])} | {fr(d['flags_conflict_among_deferring'])} | "
                 f"{fr(d['asks_confirmation_among_deferring'])} | {fr(d['cites_note_outdated_among_deferring'])} | "
                 f"{fr(d['questioned_note_among_deferring'])} | {fr(d['wrong_channel'])} |")
    L += ["", "| exploratory pairwise (measure) | A | B | risk diff, pts [95% CI] | Fisher p (uncorrected) |",
          "|---|---|---|---|---|"]
    L += [fc(c, holm_col=False) for c in pairs]
    L += [""]
    for title, key in (("Hand check (E3)", "hand_check"), ("Observations (E3)", "observations"),
                       ("Limitations (E3)", "limitations")):
        if n3.get(key):
            L += [f"### {title}", ""] + [f"- {x}" for x in n3[key]] + [""]

_out = os.path.join(RES, "summary-v4.md")
if (os.path.exists(_out) and "Corrections after independent review" in open(_out).read()
        and "--force-overwrite-corrections" not in sys.argv):
    sys.exit("summary-v4.md contains hand-made corrections after independent review (2026-11-19); regenerating would drop "
             "them. Re-apply them to this script first, or pass --force-overwrite-corrections.")
open(_out, "w").write("\n".join(L))
print("\n".join(L))
