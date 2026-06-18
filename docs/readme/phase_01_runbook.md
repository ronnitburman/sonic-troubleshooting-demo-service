# Phase 1 Runbook — Project Skeleton

## Prerequisites

- Python 3.9 or later
- `pip` available

## Step 1: Create and activate virtual environment

```bash
cd sonic-troubleshooting-demo-service
python3 -m venv .venv
source .venv/bin/activate
```

## Step 2: Install the package in editable mode

```bash
pip install -e .
```

Expected output:
```
Successfully installed sonic-troubleshooting-demo-service-0.1.0
```

## Step 3: Verify compilation

```bash
python3 -m py_compile sonic_troubleshooting_demo_service/__init__.py
```

No output = success.

## Step 4: Verify version is importable

```bash
python3 -c "import sonic_troubleshooting_demo_service; print(sonic_troubleshooting_demo_service.__version__)"
```

Expected output:
```
0.1.0
```

## Step 5: Verify entry point is registered

```bash
which sonic-troubleshooting-demo-service
```

Expected: path ending in `.venv/bin/sonic-troubleshooting-demo-service`

(Note: `sonic-troubleshooting-demo-service --help` will fail at this phase — `main.py` doesn't exist yet.)

## Phase 1 checklist

- [ ] `.venv/` directory exists
- [ ] `pyproject.toml` exists with correct metadata
- [ ] `sonic_troubleshooting_demo_service/__init__.py` exports `__version__`
- [ ] `pip install -e .` succeeds
- [ ] `python3 -m py_compile sonic_troubleshooting_demo_service/__init__.py` passes
- [ ] `__version__` is `0.1.0`
