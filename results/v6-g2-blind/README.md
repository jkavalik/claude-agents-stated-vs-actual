# v6 G2 blinded hand classification

- `shard1..4.txt`: the blinded packets (random R-ids; model, cell label and prompt pointer removed; model IDs scrubbed).
- `out1..4.jsonl`: the four classifiers' labels (each true label carries a verbatim quote).
- `key-shards.json`: R-id -> run_id, model, cell; `overlap` = the 40 runs given to two classifiers.
- `check.txt` / `check.jsonl`: the targeted agreement packet (new Q-ids) and the fresh classifier's labels.
- `key-check.json`: Q-id -> R-id, with the sampled groups.
- The cross-vendor relabel of `check.txt` by gpt-6.2-sol is in `../v6-xlabel/labels-gpt-6.2-sol.jsonl`.

The folder `results/v6-g2-handclass/` (local only, not part of this record) is a different, earlier label set that the
v6 report does not use.
