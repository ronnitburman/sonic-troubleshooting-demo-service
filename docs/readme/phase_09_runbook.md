# Phase 9 Runbook — Documentation & Final Validation

## Documentation created

| File | Purpose |
|------|---------|
| `README.md` | Project overview, architecture, commands, safety, interview points |
| `docs/DEMO_FLOW.md` | Step-by-step demo walkthrough (7 steps) |
| `docs/SONIC_BUILDIMAGE_NOTES.md` | Optional future sonic-buildimage integration |
| `docs/TROUBLESHOOTING.md` | Common issues and fixes |

## Final validation checklist

### Compilation (runs anywhere)

```bash
source .venv/bin/activate
python3 -m py_compile sonic_troubleshooting_demo_service/*.py
echo "Exit: $?  (should be 0)"
```

### Editable install

```bash
source .venv/bin/activate
pip install -e . 2>&1 | tail -3
```

### CLI help

```bash
source .venv/bin/activate
sonic-troubleshooting-demo-service --help
sonic-troubleshooting-demo-service inspect --help
sonic-troubleshooting-demo-service check --help
sonic-troubleshooting-demo-service remediate --help
```

### CLI commands on dev machine (graceful degradation)

```bash
source .venv/bin/activate

# Should show empty tables or error messages — shouldn't crash
sonic-troubleshooting-demo-service inspect --port Ethernet0
echo "Exit: $?"

sonic-troubleshooting-demo-service check --port Ethernet0
echo "Exit: $?"

sonic-troubleshooting-demo-service remediate --port Ethernet0 --dry-run
echo "Exit: $?"
```

### CLI commands on SONiC VS

```bash
# Run ALL of these with sudo on SONiC VS:

# 1. Inspect
sudo sonic-troubleshooting-demo-service inspect --port Ethernet0

# 2. Check
sudo sonic-troubleshooting-demo-service check --port Ethernet0

# 3. Remediate (dry run)
sudo sonic-troubleshooting-demo-service remediate --port Ethernet0 --dry-run

# 4. Remediate (full, with restore)
sudo sonic-troubleshooting-demo-service remediate \
  --port Ethernet0 \
  --target-status down \
  --write-mode cli \
  --restore \
  --hold-seconds 5

# 5. Remediate (Redis mode)
sudo sonic-troubleshooting-demo-service remediate \
  --port Ethernet0 \
  --target-status down \
  --write-mode redis \
  --restore \
  --hold-seconds 3
```

### Debian package build (Debian/Ubuntu)

```bash
dpkg-buildpackage -us -uc -b
ls -la ../sonic-troubleshooting-demo-service_0.1.0-1_all.deb
```

### Debian package install (SONiC VS)

```bash
sudo dpkg -i sonic-troubleshooting-demo-service_0.1.0-1_all.deb
sudo systemctl daemon-reload
which sonic-troubleshooting-demo-service
```

### Systemd service (SONiC VS)

```bash
sudo systemctl start sonic-troubleshooting-demo-service
sudo systemctl status sonic-troubleshooting-demo-service --no-pager
journalctl -u sonic-troubleshooting-demo-service -n 100 --no-pager
```

### Demo scripts (SONiC VS)

```bash
./scripts/demo_01_before.sh Ethernet0
./scripts/demo_02_run_manual.sh Ethernet0
./scripts/demo_04_after.sh Ethernet0
./scripts/demo_03_run_systemd.sh
```

### Documentation

```bash
# Verify all docs exist
ls -la README.md
ls -la docs/DEMO_FLOW.md
ls -la docs/SONIC_BUILDIMAGE_NOTES.md
ls -la docs/TROUBLESHOOTING.md
ls -la DESIGN_DECISIONS.md
ls -la CODE_FLOW.md
```

## Definition of Done (from implementation plan)

1. ✅ `python3 -m py_compile sonic_troubleshooting_demo_service/*.py` passes
2. ✅ `pip install -e .` works
3. ✅ `sonic-troubleshooting-demo-service --help` works
4. ⬜ `inspect` works on SONiC VS
5. ⬜ `check` works on SONiC VS
6. ⬜ `remediate` works on SONiC VS
7. ⬜ `.deb` package builds
8. ⬜ `.deb` package installs on SONiC VS
9. ⬜ `systemctl start sonic-troubleshooting-demo-service` works
10. ⬜ `journalctl` shows original state, applied change, verification, restore, and success

Items 4-10 require a SONiC VS environment or Debian build machine. Items 1-3 are validated on this dev machine.

## All files summary

```
sonic-troubleshooting-demo-service/
├── README.md                                  ← NEW
├── DESIGN_DECISIONS.md
├── CODE_FLOW.md
├── .gitignore
├── pyproject.toml
├── sonic_troubleshooting_demo_service/
│   ├── __init__.py
│   ├── db_constants.py
│   ├── db_config_loader.py
│   ├── redis_client.py
│   ├── command_runner.py
│   ├── port_inspector.py
│   ├── checks.py
│   ├── remediation.py
│   └── main.py
├── systemd/
│   └── sonic-troubleshooting-demo-service.service
├── scripts/
│   ├── demo_01_before.sh
│   ├── demo_02_run_manual.sh
│   ├── demo_03_run_systemd.sh
│   └── demo_04_after.sh
├── debian/
│   ├── changelog
│   ├── compat
│   ├── control
│   ├── install
│   └── rules
└── docs/
    ├── DEMO_FLOW.md                            ← NEW
    ├── SONIC_BUILDIMAGE_NOTES.md               ← NEW
    ├── TROUBLESHOOTING.md                      ← NEW
    ├── HUMAN_PLAN.md
    ├── LLM_IMPLEMENTATION_PLAN.md
    ├── phases/
    │   ├── phase_01_project_skeleton.md
    │   ├── phase_02_database_config.md
    │   ├── phase_03_redis_client.md
    │   ├── phase_04_command_runner_port_inspector.md
    │   ├── phase_05_checks_remediation.md
    │   ├── phase_06_cli_interface.md
    │   ├── phase_06_to_07_transition.md
    │   ├── phase_07_systemd_and_scripts.md
    │   ├── phase_07_to_08_transition.md
    │   ├── phase_08_debian_packaging.md
    │   └── phase_09_documentation_validation.md
    └── readme/
        ├── phase_01_runbook.md
        ├── phase_02_runbook.md
        ├── phase_03_runbook.md
        ├── phase_04_runbook.md
        ├── phase_05_runbook.md
        ├── phase_06_runbook.md
        ├── phase_07_runbook.md
        └── phase_08_runbook.md
```
