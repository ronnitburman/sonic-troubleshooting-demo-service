# Phase 7 Runbook — Systemd Service & Demo Scripts

## Files created

```
systemd/sonic-troubleshooting-demo-service.service
scripts/demo_01_before.sh
scripts/demo_02_run_manual.sh
scripts/demo_03_run_systemd.sh
scripts/demo_04_after.sh
```

## Test 1: Bash syntax check (works anywhere)

```bash
bash -n scripts/demo_01_before.sh
bash -n scripts/demo_02_run_manual.sh
bash -n scripts/demo_03_run_systemd.sh
bash -n scripts/demo_04_after.sh
echo "✓ All scripts pass syntax check"
```

## Test 2: Scripts are executable

```bash
ls -la scripts/
```

All should show `-rwxr-xr-x` (executable).

## Test 3: Service file content check

```bash
cat systemd/sonic-troubleshooting-demo-service.service
```

Expected:
```ini
[Unit]
Description=SONiC Troubleshooting Demo Service
After=database.service
Requires=database.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/sonic-troubleshooting-demo-service remediate --port Ethernet0 --target-status down --write-mode cli --restore --hold-seconds 5
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
```

Verify:
- [ ] `Type=oneshot` (not `simple` or `forking`)
- [ ] `RemainAfterExit=no`
- [ ] `ExecStart` includes `--restore`
- [ ] `Requires=database.service`

## Test 4: Demo scripts work end-to-end on SONiC VS

### Step 1: Install the package first

```bash
# If installed via pip:
pip install -e .
# OR if installed via .deb (Phase 8):
sudo dpkg -i sonic-troubleshooting-demo-service_0.1.0-1_all.deb
```

### Step 2: Show before state

```bash
./scripts/demo_01_before.sh Ethernet0
```

Expected output:
```
=== show interfaces status ===
  Interface    ...    Admin
  Ethernet0    ...    up
  ...

=== CONFIG_DB admin_status ===
up
```

### Step 3: Run manual remediation

```bash
./scripts/demo_02_run_manual.sh Ethernet0
```

Expected output:
```
┌──────────────────────────────────────┐
│ Remediation Result — Ethernet0       │
├────────────────┬─────────────────────┤
│ Original status│ up                  │
│ Target status  │ down                │
│ Final status   │ up                  │
│ Success        │ ✓                   │
└────────────────┴─────────────────────┘
Messages:
  • Applied admin_status=down to Ethernet0 via cli
  • Verified admin_status=down for Ethernet0
  • Restored admin_status=up to Ethernet0
  • Final verified admin_status=up for Ethernet0
```

### Step 4: Verify port was restored

```bash
./scripts/demo_04_after.sh Ethernet0
```

Expected output: Same as `demo_01` — `admin_status: up`.

### Step 5: Run via systemd

```bash
# Copy service file (or install via .deb)
sudo cp systemd/sonic-troubleshooting-demo-service.service /lib/systemd/system/
sudo systemctl daemon-reload

# Run
./scripts/demo_03_run_systemd.sh
```

Expected output:
```
● sonic-troubleshooting-demo-service.service - SONiC Troubleshooting Demo Service
   Loaded: loaded
   Active: inactive (dead)

... journalctl shows:
  Applied admin_status=down to Ethernet0 via cli
  Verified admin_status=down for Ethernet0
  Restored admin_status=up to Ethernet0
  Final verified admin_status=up for Ethernet0
```

## Test 5: Full demo sequence (the interview flow)

```bash
# 1. Show initial state
echo "=== STEP 1: Before ==="
./scripts/demo_01_before.sh Ethernet0

# 2. Run manual remediation
echo "=== STEP 2: Manual remediation ==="
./scripts/demo_02_run_manual.sh Ethernet0

# 3. Verify restored
echo "=== STEP 3: After ==="
./scripts/demo_04_after.sh Ethernet0

# 4. Systemd version
echo "=== STEP 4: Systemd ==="
./scripts/demo_03_run_systemd.sh
```

## Phase 7 checklist

- [ ] `systemd/` directory exists
- [ ] `sonic-troubleshooting-demo-service.service` has `Type=oneshot`
- [ ] Service file includes `--restore` in ExecStart
- [ ] Service file has `After=database.service` and `Requires=database.service`
- [ ] `scripts/` directory exists with 4 files
- [ ] All 4 scripts are executable (`chmod +x`)
- [ ] All 4 scripts pass `bash -n` syntax check
- [ ] `demo_01_before.sh` and `demo_04_after.sh` are identical (before=after proves restore works)
- [ ] `demo_02_run_manual.sh` runs the same `remediate` command as Phase 6 CLI
- [ ] `demo_03_run_systemd.sh` starts the systemd service and shows journal logs
- [ ] On SONiC VS: all 4 scripts run successfully in sequence
- [ ] On SONiC VS: `journalctl -u sonic-troubleshooting-demo-service` shows the full remediation flow
