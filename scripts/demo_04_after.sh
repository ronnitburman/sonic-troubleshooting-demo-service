#!/usr/bin/env bash
set -e

PORT="${1:-Ethernet0}"

echo "=== show interfaces status ==="
show interfaces status || true

echo
echo "=== CONFIG_DB admin_status ==="
redis-cli -s /var/run/redis/redis.sock -n 4 HGET "PORT|${PORT}" admin_status
