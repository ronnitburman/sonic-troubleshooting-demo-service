# Phase 6 Runbook — CLI Interface

## Quick start

```bash
source .venv/bin/activate
pip install -e .
sonic-troubleshooting-demo-service --help
```

## Test 1: --help for all commands

```bash
# Main help
sonic-troubleshooting-demo-service --help

# Subcommand help
sonic-troubleshooting-demo-service inspect --help
sonic-troubleshooting-demo-service check --help
sonic-troubleshooting-demo-service remediate --help
```

Expected: All four show Typer-generated help text with options.

## Test 2: inspect (dev machine, no Redis)

```bash
sonic-troubleshooting-demo-service inspect --port Ethernet0
```

Expected: Empty CONFIG_DB table (no Redis available, graceful).

## Test 3: check (dev machine, no Redis)

```bash
sonic-troubleshooting-demo-service check --port Ethernet0
```

Expected:
```
ERROR
  CONFIG_PORT_KEY_MISSING
    No CONFIG_DB entry found for port Ethernet0
    port: Ethernet0
```

"ERROR" should be in **bold red**.

## Test 4: remediate --dry-run

```bash
sonic-troubleshooting-demo-service remediate --port Ethernet0 --dry-run
```

Expected: Rich summary table with success=✓, messages showing `[DRY RUN]`, and findings.

## Test 5: inspect on SONiC VS

```bash
# On SONiC VS:
sudo sonic-troubleshooting-demo-service inspect --port Ethernet0
```

Expected: Rich table with CONFIG_DB fields:
```
┌──────────────────────────────────────┐
│ CONFIG_DB — PORT|Ethernet0           │
├───────────────┬──────────────────────┤
│ admin_status  │ up                   │
│ mtu           │ 9100                 │
│ ...           │ ...                  │
└───────────────┴──────────────────────┘
```

## Test 6: check on SONiC VS

```bash
# On SONiC VS:
sudo sonic-troubleshooting-demo-service check --port Ethernet0
```

Expected (healthy port):
```
✓ No issues found for port Ethernet0
```

Expected (admin down port):
```
INFO
  PORT_ADMIN_DOWN
    Port Ethernet0 is administratively down
    port: Ethernet0
    admin_status: down
```

## Test 7: remediate on SONiC VS (full flow)

```bash
# On SONiC VS:
sudo sonic-troubleshooting-demo-service remediate \
  --port Ethernet0 \
  --target-status down \
  --write-mode cli \
  --restore \
  --hold-seconds 5
```

Expected output:
```
┌──────────────────────────────────────┐
│ Remediation Result — Ethernet0       │
├────────────────┬─────────────────────┤
│ Field          │ Value               │
│ Port           │ Ethernet0           │
│ Original status│ up                  │
│ Target status  │ down                │
│ Write mode     │ cli                 │
│ Restore        │ True                │
│ Final status   │ up                  │
│ Success        │ ✓                   │
└────────────────┴─────────────────────┘

Messages:
  • Applied admin_status=down to Ethernet0 via cli
  • Verified admin_status=down for Ethernet0
  • Restored admin_status=up to Ethernet0
  • Final verified admin_status=up for Ethernet0
```

## Test 8: remediate --no-restore (careful!)

```bash
# On SONiC VS — leaves port down!
sudo sonic-troubleshooting-demo-service remediate \
  --port Ethernet0 \
  --target-status down \
  --write-mode cli \
  --no-restore

# Manually restore:
sudo sonic-troubleshooting-demo-service remediate \
  --port Ethernet0 \
  --target-status up \
  --write-mode cli \
  --no-restore
```

## Test 9: remediate with Redis mode

```bash
# On SONiC VS:
sudo sonic-troubleshooting-demo-service remediate \
  --port Ethernet0 \
  --target-status down \
  --write-mode redis \
  --restore \
  --hold-seconds 3
```

Same output format as CLI mode.

## Test 10: Exit codes

```bash
# Dry run succeeds
sonic-troubleshooting-demo-service remediate --port Ethernet0 --dry-run
echo "Exit code: $?"

# Actual run fails without Redis/CLI
sonic-troubleshooting-demo-service remediate --port Ethernet0 --target-status down
echo "Exit code: $?"
```

Expected: Dry run exits 0. Failed run exits 1.

## Phase 6 checklist

- [ ] `main.py` compiles and imports
- [ ] `pip install -e .` registers the console_scripts entry point
- [ ] `sonic-troubleshooting-demo-service --help` shows 3 commands
- [ ] `inspect --help`, `check --help`, `remediate --help` all show options
- [ ] `inspect` produces Rich tables (empty on dev, populated on SONiC VS)
- [ ] `check` shows color-coded findings grouped by severity
- [ ] `check` shows green success message when no findings
- [ ] `remediate --dry-run` shows summary without side effects
- [ ] `remediate` exit code 0 on success, 1 on failure
- [ ] On SONiC VS: all three commands work with `sudo`
- [ ] Rich output: tables, colors, severity headings
