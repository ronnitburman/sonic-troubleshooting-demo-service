# Phase 8 Runbook — Debian Packaging

## Prerequisites

Debian/Ubuntu build machine with:
```bash
sudo apt-get install -y debhelper dh-python python3-all python3-setuptools build-essential dpkg-dev
```

## Files created

```
debian/
├── changelog    (version 0.1.0-1 — matches pyproject.toml)
├── compat       (debhelper level 10)
├── control      (Architecture: all, Depends: python3-redis, python3-typer, python3-rich)
├── rules        (dh $@ --with python3 --buildsystem=pybuild)
└── install      (systemd unit → /lib/systemd/system/)
```

## Test 1: Validate file contents (works anywhere)

```bash
source .venv/bin/activate
python3 -c "
import re

# Check version consistency
with open('pyproject.toml') as f:
    toml = f.read()
m = re.search(r'version\s*=\s*\"([^\"]+)\"', toml)
py_ver = m.group(1) if m else 'NOT FOUND'

with open('debian/changelog') as f:
    cl = f.read()
m = re.search(r'\(([^)]+)\)', cl)
deb_ver = m.group(1) if m else 'NOT FOUND'

print(f'pyproject.toml: {py_ver}')
print(f'debian/changelog: {deb_ver}')
assert py_ver in deb_ver, f'VERSION MISMATCH'
print('✓ Versions match')

# Check control fields
with open('debian/control') as f:
    ctrl = f.read()
for fld in ['Source:', 'Architecture: all', 'Depends:', 'python3-redis', 'python3-typer', 'python3-rich']:
    assert fld in ctrl, f'Missing: {fld}'
print('✓ All required control fields present')

# Check rules
with open('debian/rules') as f:
    rules = f.read()
assert 'dh ' in rules and 'pybuild' in rules
print('✓ Rules file valid')

# Check install
with open('debian/install') as f:
    inst = f.read()
assert 'systemd/' in inst and 'lib/systemd/system' in inst
print('✓ Install file valid')

print()
print('✓ All debian/ files validated')
"
```

## Test 2: Build the package (Debian/Ubuntu only)

```bash
# Clean previous builds
rm -rf debian/.debhelper debian/sonic-troubleshooting-demo-service debian/files debian/*.log debian/*.substvars

# Build
dpkg-buildpackage -us -uc -b
```

Expected output ends with:
```
dpkg-deb: building package 'sonic-troubleshooting-demo-service' in '../sonic-troubleshooting-demo-service_0.1.0-1_all.deb'
```

## Test 3: Verify the artifact

```bash
# Check it exists
ls -la ../sonic-troubleshooting-demo-service_0.1.0-1_all.deb

# List contents
dpkg-deb -c ../sonic-troubleshooting-demo-service_0.1.0-1_all.deb
```

Expected contents:
```
/usr/lib/python3/dist-packages/sonic_troubleshooting_demo_service/
    __init__.py
    db_constants.py
    db_config_loader.py
    redis_client.py
    command_runner.py
    port_inspector.py
    checks.py
    remediation.py
    main.py
/usr/local/bin/sonic-troubleshooting-demo-service
/lib/systemd/system/sonic-troubleshooting-demo-service.service
```

## Test 4: Check metadata

```bash
dpkg-deb -I ../sonic-troubleshooting-demo-service_0.1.0-1_all.deb
```

Expected:
```
 Package: sonic-troubleshooting-demo-service
 Version: 0.1.0-1
 Architecture: all
 Depends: python3, python3-redis, python3-typer, python3-rich
```

## Test 5: Install on SONiC VS

```bash
# Copy to SONiC VS
scp ../sonic-troubleshooting-demo-service_0.1.0-1_all.deb admin@<sonic-vs-ip>:~/

# SSH in
ssh admin@<sonic-vs-ip>

# Install
sudo dpkg -i sonic-troubleshooting-demo-service_0.1.0-1_all.deb

# If dependency errors (SONiC VS may lack python3-typer as apt package):
sudo pip3 install redis typer rich python-dotenv
sudo dpkg --force-depends -i sonic-troubleshooting-demo-service_0.1.0-1_all.deb

# Reload systemd
sudo systemctl daemon-reload
```

## Test 6: Verify installation

```bash
# Binary on PATH
which sonic-troubleshooting-demo-service
# Expected: /usr/local/bin/sonic-troubleshooting-demo-service

# Help
sonic-troubleshooting-demo-service --help

# Inspect
sudo sonic-troubleshooting-demo-service inspect --port Ethernet0

# Check
sudo sonic-troubleshooting-demo-service check --port Ethernet0

# Remediate dry run
sudo sonic-troubleshooting-demo-service remediate --port Ethernet0 --dry-run

# Full remediation
sudo sonic-troubleshooting-demo-service remediate \
  --port Ethernet0 \
  --target-status down \
  --write-mode cli \
  --restore \
  --hold-seconds 5
```

## Test 7: Systemd service (from installed .deb)

```bash
# Start service
sudo systemctl start sonic-troubleshooting-demo-service

# Check status
sudo systemctl status sonic-troubleshooting-demo-service --no-pager

# View logs
journalctl -u sonic-troubleshooting-demo-service -n 50 --no-pager

# Verify service file location
ls -la /lib/systemd/system/sonic-troubleshooting-demo-service.service
```

## Test 8: Uninstall

```bash
# Remove package
sudo dpkg -r sonic-troubleshooting-demo-service

# Verify removed
which sonic-troubleshooting-demo-service  # Should fail
ls /lib/systemd/system/sonic-troubleshooting-demo-service.service  # Should fail

# Reinstall
sudo dpkg -i sonic-troubleshooting-demo-service_0.1.0-1_all.deb
sudo systemctl daemon-reload
```

## Phase 8 checklist

- [ ] `debian/control` has all required fields
- [ ] `debian/changelog` version matches `pyproject.toml` (0.1.0)
- [ ] `debian/compat` is `10`
- [ ] `debian/rules` is executable and contains `dh $@ --with python3 --buildsystem=pybuild`
- [ ] `debian/install` maps service file to `lib/systemd/system/`
- [ ] `dpkg-buildpackage -us -uc -b` exits 0
- [ ] `.deb` artifact exists: `../sonic-troubleshooting-demo-service_0.1.0-1_all.deb`
- [ ] `dpkg-deb -c` shows all 9 .py files, console script, and systemd unit
- [ ] `dpkg-deb -I` shows correct dependencies
- [ ] `sudo dpkg -i` succeeds on SONiC VS
- [ ] `which sonic-troubleshooting-demo-service` finds the binary
- [ ] `inspect`, `check`, `remediate` work from installed package
- [ ] `systemctl start sonic-troubleshooting-demo-service` works
- [ ] `journalctl` shows remediation flow
