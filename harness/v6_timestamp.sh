#!/usr/bin/env bash
# Independent timestamp of a pushed pre-registration commit (brief v6, section 4): writes results/timestamps/<commit>.txt
# (the commit hash and the PREREG.md sha256 at that commit) and an OpenTimestamps proof <commit>.txt.ots next to it.
# The proof is pending until a Bitcoin block confirms it (hours); run `ots upgrade` on it later to complete it.
# Usage: harness/v6_timestamp.sh <full-commit-hash>
set -euo pipefail
C="$1"; S="${OTS_HOME:?set OTS_HOME to the directory holding ots-venv/ (the OpenTimestamps client)}"
cd "$(dirname "$0")/.."; mkdir -p results/timestamps
H=$(git -C publish/alignment-testing show "$C:results/PREREG.md" | sha256sum | cut -c1-64)
printf 'repository: github.com/jkavalik/claude-agents-stated-vs-actual\ncommit: %s\nresults/PREREG.md sha256 at that commit: %s\n' "$C" "$H" > "results/timestamps/$C.txt"
HOME="$S" "$S/ots-venv/bin/ots" stamp "results/timestamps/$C.txt"
echo "stamped results/timestamps/$C.txt (PREREG sha256 $H)"
