# Phase 5 Runbook — Checks & Remediation

## Test 1: checks.py (unit tests — works anywhere)

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.checks import run_port_checks
from sonic_troubleshooting_demo_service.port_inspector import PortView

def make_view(port='Ethernet0', config=None):
    return PortView(port=port, config_key=f'PORT|{port}',
                    config_db=config or {}, appl_db={}, state_db={})

# Empty config → CONFIG_PORT_KEY_MISSING (error)
v = make_view(config={})
f = run_port_checks(v)
assert len(f) == 1 and f[0].code == 'CONFIG_PORT_KEY_MISSING'
print('✓ Empty config → CONFIG_PORT_KEY_MISSING')

# Missing admin_status → ADMIN_STATUS_MISSING (error)
v = make_view(config={'mtu': '9100'})
f = run_port_checks(v)
assert any(x.code == 'ADMIN_STATUS_MISSING' for x in f)
print('✓ No admin_status → ADMIN_STATUS_MISSING')

# Invalid admin_status → ADMIN_STATUS_INVALID (error)
v = make_view(config={'admin_status': 'bogus', 'mtu': '9100'})
f = run_port_checks(v)
assert any(x.code == 'ADMIN_STATUS_INVALID' for x in f)
print('✓ Bogus admin_status → ADMIN_STATUS_INVALID')

# Admin down → PORT_ADMIN_DOWN (info)
v = make_view(config={'admin_status': 'down', 'mtu': '9100'})
f = run_port_checks(v)
assert any(x.code == 'PORT_ADMIN_DOWN' for x in f)
print('✓ Admin down → PORT_ADMIN_DOWN (info)')

# Missing MTU → MTU_MISSING (warning)
v = make_view(config={'admin_status': 'up'})
f = run_port_checks(v)
assert any(x.code == 'MTU_MISSING' for x in f)
print('✓ Missing MTU → MTU_MISSING (warning)')

# Healthy port → nothing
v = make_view(config={'admin_status': 'up', 'mtu': '9100'})
f = run_port_checks(v)
assert f == []
print('✓ Healthy port → no findings')

print()
print('✓ All checks.py tests passed')
"
```

### Expected output

```
✓ Empty config → CONFIG_PORT_KEY_MISSING
✓ No admin_status → ADMIN_STATUS_MISSING
✓ Bogus admin_status → ADMIN_STATUS_INVALID
✓ Admin down → PORT_ADMIN_DOWN (info)
✓ Missing MTU → MTU_MISSING (warning)
✓ Healthy port → no findings

✓ All checks.py tests passed
```

## Test 2: remediation.py (API surface — works anywhere)

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.remediation import PortRemediationService

svc = PortRemediationService()

# Input validation
try:
    svc._validate_inputs('bogus', 'cli')
except ValueError as e:
    print('✓ Bad target_status rejected:', e)

try:
    svc._validate_inputs('up', 'bogus')
except ValueError as e:
    print('✓ Bad write_mode rejected:', e)

svc._validate_inputs('up', 'cli')
svc._validate_inputs('down', 'redis')
print('✓ Valid inputs accepted')

# Dry run (works without config command or Redis)
result = svc.remediate(
    port='Ethernet0', target_status='down', write_mode='cli',
    restore=True, hold_seconds=1, dry_run=True,
)
print(f'Dry run: port={result.port}, success={result.success}')
print(f'  messages: {result.messages}')
print(f'  findings_before: {len(result.findings_before)}')

# CLI mode without config command should fail
try:
    svc.remediate(port='Ethernet0', target_status='down',
                  write_mode='cli', restore=False, dry_run=False)
except RuntimeError as e:
    print(f'✓ Missing config command rejected: {str(e)[:50]}...')

print()
print('✓ All remediation.py tests passed')
"
```

### Expected output

```
✓ Bad target_status rejected: target_status must be 'up' or 'down'...
✓ Bad write_mode rejected: write_mode must be 'cli' or 'redis'...
✓ Valid inputs accepted
Dry run: port=Ethernet0, success=True
  messages: ['[DRY RUN] No changes applied.']
  findings_before: 1
✓ Missing config command rejected: CLI write mode requires the 'config' comm...
```

## Test 3: Remediation with Redis mode (requires Redis on Unix socket)

Only works on SONiC VS or a machine with Redis running on `/var/run/redis/redis.sock`.

```bash
# On SONiC VS:
source .venv/bin/activate
sudo python3 -c "
import logging
logging.basicConfig(level=logging.INFO)

from sonic_troubleshooting_demo_service.remediation import PortRemediationService

svc = PortRemediationService()

# Dry run first
print('=== DRY RUN ===')
result = svc.remediate(
    port='Ethernet0', target_status='down', write_mode='redis',
    restore=True, hold_seconds=2, dry_run=True
)
print(f'Original: {result.original_status}')
print(f'Findings before: {len(result.findings_before)}')
print()

# Real run with Redis mode (no-op: set to same value for safety)
print('=== REAL (Redis mode, no-op) ===')
result = svc.remediate(
    port='Ethernet0', target_status='up', write_mode='redis',
    restore=True, hold_seconds=2, dry_run=False
)
print(f'Original: {result.original_status}')
print(f'Target: {result.target_status}')
print(f'Final: {result.final_status}')
print(f'Restored: {result.restored}')
print(f'Success: {result.success}')
for msg in result.messages:
    print(f'  • {msg}')

# Full remediation with restore (Redis mode)
print()
print('=== REAL (Redis mode, toggle + restore) ===')
original = result.original_status or 'up'
target = 'down' if original == 'up' else 'up'
result = svc.remediate(
    port='Ethernet0', target_status=target, write_mode='redis',
    restore=True, hold_seconds=3, dry_run=False
)
print(f'Original: {result.original_status} → Target: {result.target_status} → Final: {result.final_status}')
print(f'Restored: {result.restored}, Success: {result.success}')
print(f'Findings before: {len(result.findings_before)}, after: {len(result.findings_after)}')

print()
print('✓ SONiC VS remediation test complete')
"
```

## Test 4: Full remediation with CLI mode (requires SONiC VS)

```bash
# On SONiC VS:
source .venv/bin/activate
sudo python3 -c "
from sonic_troubleshooting_demo_service.remediation import PortRemediationService

svc = PortRemediationService()
result = svc.remediate(
    port='Ethernet0', target_status='down', write_mode='cli',
    restore=True, hold_seconds=5, dry_run=False
)
print(f'Success: {result.success}')
print(f'Original: {result.original_status} → Target: {result.target_status} → Final: {result.final_status}')
for msg in result.messages:
    print(f'  • {msg}')
"
```

Expected: `success=True`, `original_status=up`, `final_status=up` (restored).

### Test no-restore mode

```bash
# On SONiC VS:
sudo python3 -c "
from sonic_troubleshooting_demo_service.remediation import PortRemediationService

svc = PortRemediationService()
result = svc.remediate(
    port='Ethernet0', target_status='down', write_mode='cli',
    restore=False, hold_seconds=2, dry_run=False
)
print(f'Success: {result.success}, Restored: {result.restored}')
print(f'Final status: {result.final_status}')
print('WARNING: Port may still be down! Manually restore if needed.')
print('  Run: sudo config interface startup Ethernet0')
"
```

## Phase 5 checklist

- [ ] `checks.py` compiles
- [ ] `remediation.py` compiles
- [ ] 5 checks: CONFIG_PORT_KEY_MISSING, ADMIN_STATUS_MISSING, ADMIN_STATUS_INVALID, PORT_ADMIN_DOWN, MTU_MISSING
- [ ] Empty config → CONFIG_PORT_KEY_MISSING and short-circuits
- [ ] Admin down produces info (not error) severity
- [ ] Healthy port returns empty list
- [ ] Input validation rejects bad values
- [ ] Dry run works without config command or Redis
- [ ] CLI mode requires `config` on PATH
- [ ] Redis mode writes to CONFIG_DB directly
- [ ] Restore defaults to True, restores original
- [ ] Missing original status → restores to `"up"` with warning
- [ ] Exception during remediation → captured in messages, success=False
