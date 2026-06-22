# sonic-troubleshooting-demo-service

## What this is

A small SONiC troubleshooting demo service that demonstrates safe, controlled
port state inspection and remediation. It is a Python CLI package that builds
into a Debian package, installs on SONiC VS, and runs as a `systemd` oneshot
service.

## What it demonstrates

1. **SONiC DB access** — Reading CONFIG_DB, APPL_DB, and STATE_DB via Redis
   Unix socket, with dynamic DB config loading and compiled-in fallbacks.
2. **Safe subprocess execution** — Running SONiC CLI commands without
   `shell=True`, with proper error handling.
3. **Structured troubleshooting checks** — Deterministic port health checks
   with severity levels (error, warning, info).
4. **Controlled remediation** — Applying port admin state changes via CLI or
   Redis direct write, verifying the change, and always restoring the original
   state by default.
5. **Systemd oneshot integration** — A non-daemon service that runs once,
   performs its task, and exits cleanly.
6. **Debian packaging** — Standalone `.deb` build with `dpkg-buildpackage`.

## Architecture

```
sonic-troubleshooting-demo-service/
├── pyproject.toml              # Package metadata and dependencies
├── sonic_troubleshooting_demo_service/
│   ├── __init__.py             # Version
│   ├── main.py                 # Typer CLI (inspect, check, remediate)
│   ├── db_constants.py         # Fallback DB definitions
│   ├── db_config_loader.py     # Dynamic DB config from JSON
│   ├── redis_client.py         # Redis client over Unix socket
│   ├── command_runner.py       # Safe subprocess execution
│   ├── port_inspector.py       # Multi-DB port state reader
│   ├── checks.py               # Troubleshooting check rules
│   └── remediation.py          # Remediation orchestration
├── systemd/
│   └── sonic-troubleshooting-demo-service.service
├── debian/                     # Debian packaging files
├── scripts/                    # Demo scripts
└── docs/                       # Documentation
```

### Layered design

```
┌─────────────────────────────────────────┐
│  main.py        CLI (Typer + Rich)       │  ← User-facing layer
├─────────────────────────────────────────┤
│  remediation.py  checks.py               │  ← Business logic layer
├─────────────────────────────────────────┤
│  port_inspector.py  command_runner.py    │  ← Infrastructure layer
├─────────────────────────────────────────┤
│  redis_client.py  db_config_loader.py    │  ← Data access layer
│  db_constants.py                         │
└─────────────────────────────────────────┘
```

## Commands

### inspect

Reads CONFIG_DB, APPL_DB, and STATE_DB for the given port and displays
Rich-formatted tables.

```bash
sudo sonic-troubleshooting-demo-service inspect --port Ethernet0
```

### check

Runs troubleshooting checks and reports findings grouped by severity
(error, warning, info).

```bash
sudo sonic-troubleshooting-demo-service check --port Ethernet0
```

### remediate

Changes port admin status, verifies it, holds for N seconds, then restores
the original status. Supports `--dry-run` to preview without changes.

```bash
sudo sonic-troubleshooting-demo-service remediate \
  --port Ethernet0 \
  --target-status down \
  --write-mode cli \
  --restore \
  --hold-seconds 5
```

## Build

```bash
# Install build dependencies (Debian/Ubuntu)
sudo apt-get install -y debhelper dh-python python3-all python3-setuptools build-essential

# Build the .deb
dpkg-buildpackage -us -uc -b
```

Expected artifact: `../sonic-troubleshooting-demo-service_0.1.0-1_all.deb`

## Install on SONiC VS

```bash
sudo dpkg -i sonic-troubleshooting-demo-service_0.1.0-1_all.deb
sudo systemctl daemon-reload
```

## Run as systemd service

```bash
sudo systemctl start sonic-troubleshooting-demo-service
sudo systemctl status sonic-troubleshooting-demo-service --no-pager
journalctl -u sonic-troubleshooting-demo-service -n 100 --no-pager
```

## Demo flow

Run the four demo scripts in sequence:

```bash
./scripts/demo_01_before.sh Ethernet0    # Show initial state
./scripts/demo_02_run_manual.sh Ethernet0 # Run remediation via CLI
./scripts/demo_04_after.sh Ethernet0     # Verify state is restored
```

After package install:

```bash
./scripts/demo_03_run_systemd.sh         # Run via systemd
```

## CLI mode vs Redis mode

| Aspect | CLI mode | Redis mode |
|--------|----------|------------|
| Method | `config interface shutdown/startup` | `HSET CONFIG_DB PORT\|<port> admin_status` |
| SONiC awareness | Full (runs through SONiC config flow) | Direct DB write only |
| Dependency | Requires `config` command on PATH | Only requires Redis socket access |
| Side effects | May trigger config reload | Bypasses config reload |
| Use case | Production-safe demo | Internal DB inspection demo |

## Safety behavior

- **Default `--restore`**: The service always restores the original port
  state by default. Use `--no-restore` explicitly to leave the port changed.
- **`--dry-run`**: Preview what would happen without making changes.
- **Validation**: Target status must be `up` or `down`; write mode must be
  `cli` or `redis`.
- **Original state fallback**: If the original admin_status cannot be read,
  the service restores to `up` with a clear warning log.
- **No `shell=True`**: All subprocess calls use argument lists.
- **Oneshot**: The systemd service runs once and exits — no persistent daemon.
- **No ASIC_DB access**: The service only touches CONFIG_DB, APPL_DB, and
  STATE_DB. ASIC_DB (db=1) is never read or written.

## sonic-buildimage notes

See [docs/SONIC_BUILDIMAGE_NOTES.md](docs/SONIC_BUILDIMAGE_NOTES.md) for optional
future integration into a full SONiC image build.

## Interview talking points

### Design philosophy
Small surface area, safe defaults, recoverable operations. Every remediation
attempt verifies and restores. The system defaults to reversible — `--restore`
is on by default.

### SONiC internals touched
CONFIG_DB, APPL_DB, STATE_DB — read-only except for the controlled
admin_status write. No ASIC_DB access. No orchagent/syncd modification.

### Extensibility
- New checks can be added by extending `checks.py`
- New write modes can be added to `remediation.py`
- New DB support requires only adding to `db_constants.py`

### Testing strategy
Each phase is independently testable. The CLI commands work both locally
(with graceful degradation when Redis is absent) and on SONiC VS.

### Why oneshot
A troubleshooting demo doesn't need a long-running daemon. Oneshot matches
the use case: run, report, exit. No resource drain between runs. Every
invocation is cleanly logged in journald.

### Security
- No `shell=True` — subprocess calls use argument lists
- Redis over Unix socket — no network exposure
- Dry-run available for pre-flight safety
- Restore is the default — accidental runs are harmless
