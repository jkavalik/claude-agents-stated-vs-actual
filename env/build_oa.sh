#!/usr/bin/env bash
# v6 images: one align-task-oa:<tag> per task image v6 uses, built on top of the existing image.
set -euo pipefail
cd "$(dirname "$0")"
for t in hard mild seen sc3x-safety sc3x-capabilities sc3x-safety_verify sc3x-capabilities_verify; do
  docker build -q --build-arg BASE=align-task:$t -f Dockerfile.oa -t align-task-oa:$t . >/dev/null && echo "built align-task-oa:$t"
done
