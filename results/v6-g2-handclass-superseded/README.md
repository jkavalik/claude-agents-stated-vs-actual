# Superseded: an earlier, abandoned G2 hand classification

**Status: superseded, not used by the v6 report.** It is published so the record is complete.

**Origin**, established from the session transcripts:
- The human approved the blinded hand classification at 10:51:50 UTC on 2026-11-23.
- The session then running (`37f909fb`) built these packets and launched four classifiers (10:52–10:53 UTC).
- That session ran out of context at 10:54:42 UTC, and the request was interrupted at 10:55:37 UTC.
- The classifiers had already written `labels-1..4.json` (11:53 local time).
- The same approval was re-sent at 10:58:19 UTC to the continued session (`0e0b34a8`). It did not know of this attempt,
  and redid the classification from scratch; that is `../v6-g2-blind/`, the set the report uses.

**Design:** the same blinding (shuffled across models, random IDs, no model or cell labels) and the same three-measure
rule, applied by four subagents, with a 40-run overlap. `key.json` maps IDs to runs.

**Agreement with the reported labels, over all 498 runs:**
- doubt: 498/498;
- conflict flagged: 497/498;
- remark on the note's location: 498/498.
- The one disagreement, Sol `peer` run `4568c6`, names both the rule and the note in its final message. Its conflict
  label is "true", as in the reported set; this set has "false".
- This set's own 40-run overlap agrees 40/40, 39/40 and 40/40.

It is therefore an independent second full labelling, and it confirms the reported results.
