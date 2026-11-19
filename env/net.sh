#!/usr/bin/env bash
# Create the networks and start the egress proxy (idempotent).
# align-internal has no route out; the proxy also sits on align-egress and is the only way out.
set -euo pipefail
docker network inspect align-internal >/dev/null 2>&1 || docker network create --internal align-internal
docker network inspect align-egress   >/dev/null 2>&1 || docker network create align-egress
if ! docker container inspect egress-proxy >/dev/null 2>&1; then
  docker run -d --name egress-proxy --network align-egress --restart unless-stopped align-proxy
  docker network connect align-internal egress-proxy
fi
