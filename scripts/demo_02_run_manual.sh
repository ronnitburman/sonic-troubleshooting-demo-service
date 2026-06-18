#!/usr/bin/env bash
set -e

PORT="${1:-Ethernet0}"

sudo sonic-troubleshooting-demo-service remediate \
  --port "${PORT}" \
  --target-status down \
  --write-mode cli \
  --restore \
  --hold-seconds 5
