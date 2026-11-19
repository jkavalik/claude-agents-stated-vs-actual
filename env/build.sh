#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
docker build -t align-proxy proxy
docker build --build-arg VARIANT=hard -t align-task:hard .
docker build --build-arg VARIANT=mild -t align-task:mild .
docker build --build-arg VARIANT=seen -t align-task:seen .
docker build --build-arg TASK=safety -f Dockerfile.sc -t align-task:sc-safety .
docker build --build-arg TASK=capabilities -f Dockerfile.sc -t align-task:sc-capabilities .
docker build --build-arg TASK=safety -f Dockerfile.sc2 -t align-task:sc2-safety .
docker build --build-arg TASK=capabilities -f Dockerfile.sc2 -t align-task:sc2-capabilities .
docker build --build-arg TASK=safety -f Dockerfile.sc3 -t align-task:sc3-safety .
docker build --build-arg TASK=capabilities -f Dockerfile.sc3 -t align-task:sc3-capabilities .
docker build --build-arg TASK=safety -f Dockerfile.sc3x -t align-task:sc3x-safety .
docker build --build-arg TASK=capabilities -f Dockerfile.sc3x -t align-task:sc3x-capabilities .
docker build --build-arg TASK=safety_neutral -f Dockerfile.sc3x -t align-task:sc3x-safety_neutral .
docker build --build-arg TASK=capabilities_neutral -f Dockerfile.sc3x -t align-task:sc3x-capabilities_neutral .
docker build --build-arg TASK=capabilities_flagword -f Dockerfile.sc3x -t align-task:sc3x-capabilities_flagword .
docker build --build-arg TASK=safety_training -f Dockerfile.sc3x -t align-task:sc3x-safety_training .
docker build --build-arg TASK=safety_alert -f Dockerfile.sc3x -t align-task:sc3x-safety_alert .
docker build --build-arg TASK=safety_midfile -f Dockerfile.sc3x -t align-task:sc3x-safety_midfile .
docker build --build-arg TASK=safety_verify -f Dockerfile.sc3x -t align-task:sc3x-safety_verify .
docker build --build-arg TASK=capabilities_verify -f Dockerfile.sc3x -t align-task:sc3x-capabilities_verify .
