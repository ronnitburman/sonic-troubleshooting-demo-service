# Phase 4 Runbook — Command Runner & Port Inspector

## Test 1: command_runner.py

### Local test (works anywhere)

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.command_runner import command_exists, run_command

# command_exists
print('command_exists(\"ls\"):', command_exists('ls'))
print('command_exists(\"bogus_cmd\"):', command_exists('bogus_cmd'))

# Successful command
out = run_command(['echo', 'hello world'])
print('echo output:', repr(out))
assert out == 'hello world'

# Failing command
try:
    run_command(['false'])
except RuntimeError as e:
    print('Correctly raised RuntimeError for exit 1')
    assert 'exit 1' in str(e)

# No shell=True in the source — verify by inspection:
# grep should find NO 'shell=True' in the file
print('✓ command_runner tests passed')
"
```

### Verify no shell=True

```bash
grep -n 'shell' sonic_troubleshooting_demo_service/command_runner.py
```

Expected: Only comments/documentation mentioning shell=True, never an actual `shell=True` argument to `subprocess.run`.

## Test 2: port_inspector.py

### Inspect on dev machine (no Redis — graceful degradation)

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.port_inspector import PortInspector

inspector = PortInspector()
view = inspector.inspect('Ethernet0')

print('port:', view.port)
print('config_key:', view.config_key)
print('config_db:', view.config_db)
print('appl_db:', view.appl_db)
print('state_db:', view.state_db)

# All should be dicts (empty on dev machine)
assert isinstance(view.config_db, dict)
assert isinstance(view.appl_db, dict)
assert isinstance(view.state_db, dict)
print('✓ All DB views are dicts (empty without Redis — expected)')
"
```

### Inspect on SONiC VS (with Redis)

```bash
# On SONiC VS:
source .venv/bin/activate
sudo python3 -c "
from sonic_troubleshooting_demo_service.port_inspector import PortInspector

inspector = PortInspector()
view = inspector.inspect('Ethernet0')

print('=== CONFIG_DB ===')
for k, v in sorted(view.config_db.items()):
    print(f'  {k}: {v}')

if view.appl_db:
    print('=== APPL_DB ===')
    for k, v in sorted(view.appl_db.items()):
        print(f'  {k}: {v}')

if view.state_db:
    print('=== STATE_DB ===')
    for k, v in sorted(view.state_db.items()):
        print(f'  {k}: {v}')

# Verify expected fields exist
assert 'admin_status' in view.config_db, 'Missing admin_status in CONFIG_DB'
print()
print('admin_status:', view.config_db['admin_status'])
print('mtu:', view.config_db.get('mtu', 'N/A'))
print('✓ SONiC VS inspect successful')
"
```

Expected output on SONiC VS:
```
=== CONFIG_DB ===
  admin_status: up
  mtu: 9100
  ... (other fields)

admin_status: up
mtu: 9100
✓ SONiC VS inspect successful
```

### Inspect non-existent port

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.port_inspector import PortInspector

inspector = PortInspector()
view = inspector.inspect('PortThatDoesNotExist999')

print('config_db:', view.config_db)
print('appl_db:', view.appl_db)
print('state_db:', view.state_db)

# Should not crash — should return empty dicts
print('✓ Non-existent port handled without crash')
"
```

### Inspect multiple ports

```bash
# On SONiC VS:
source .venv/bin/activate
sudo python3 -c "
from sonic_troubleshooting_demo_service.port_inspector import PortInspector

inspector = PortInspector()

for port in ['Ethernet0', 'Ethernet4', 'Ethernet8']:
    view = inspector.inspect(port)
    status = view.config_db.get('admin_status', 'N/A')
    print(f'{port}: admin_status={status}')
"
```

## Test 3: End-to-end (command_runner + port_inspector together)

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.command_runner import command_exists
from sonic_troubleshooting_demo_service.port_inspector import PortInspector

# Check if we're on SONiC VS
has_config = command_exists('config')
print(f'SONiC config command available: {has_config}')

inspector = PortInspector()
view = inspector.inspect('Ethernet0')

if view.config_db:
    print(f'Port Ethernet0 has config data: {len(view.config_db)} fields')
    print(f'  admin_status: {view.config_db.get(\"admin_status\")}')
else:
    print('No config data (not on SONiC or port does not exist)')
    print('This is expected on a dev machine')

print('✓ Integration test complete')
"
```

## Phase 4 checklist

- [ ] `command_runner.py` compiles
- [ ] `port_inspector.py` compiles
- [ ] `command_exists` works for real and fake commands
- [ ] `run_command` returns stdout for successful commands
- [ ] `run_command` raises `RuntimeError` for non-zero exit
- [ ] No `shell=True` in `command_runner.py`
- [ ] `PortInspector` can be instantiated
- [ ] `inspect` returns `PortView` with correct port and config_key
- [ ] `config_db`, `appl_db`, `state_db` are dicts (empty on dev machine)
- [ ] Non-existent port doesn't crash
- [ ] On SONiC VS: `config_db` contains `admin_status` and `mtu`
- [ ] On SONiC VS: `appl_db` or `state_db` may or may not have data (both acceptable)
