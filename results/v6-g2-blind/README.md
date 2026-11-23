# v6 G2 blinded hand classification

- `shard1..4.txt`: the blinded packets (random R-ids; model, cell label and prompt pointer removed; model IDs scrubbed).
- `out1..4.jsonl`: the four classifiers' labels (each true label carries a verbatim quote).
- `key-shards.json`: R-id -> run_id, model, cell; `overlap` = the 40 runs given to two classifiers.
- `check.txt` / `check.jsonl`: the targeted agreement packet (new Q-ids) and the fresh classifier's labels.
- `key-check.json`: Q-id -> R-id, with the sampled groups.
- The cross-vendor relabel of `check.txt` by gpt-6.2-sol is in `../v6-xlabel/labels-gpt-6.2-sol.jsonl`.

An earlier, abandoned labelling of the same runs is published as `../v6-g2-handclass-superseded/`, with its origin
and its agreement with this set (498/498, 497/498, 498/498).
