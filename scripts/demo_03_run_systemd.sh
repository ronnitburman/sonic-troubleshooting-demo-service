#!/usr/bin/env bash
set -e

sudo systemctl start sonic-troubleshooting-demo-service
sudo systemctl status sonic-troubleshooting-demo-service --no-pager || true
journalctl -u sonic-troubleshooting-demo-service -n 100 --no-pager
