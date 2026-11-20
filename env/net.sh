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

# v6 (OpenAI): a separate internal network whose only way out is a proxy that allows api.openai.com and nothing else.
# The Anthropic proxy is not on this network, so v6 agents cannot reach it.
docker network inspect align-internal-oa >/dev/null 2>&1 || docker network create --internal align-internal-oa
if ! docker container inspect egress-proxy-openai >/dev/null 2>&1; then
  docker run -d --name egress-proxy-openai --network align-egress --restart unless-stopped \
    -v "$(cd "$(dirname "$0")" && pwd)/proxy-openai/filter:/etc/tinyproxy/filter:ro" align-proxy
  docker network connect align-internal-oa egress-proxy-openai
fi
