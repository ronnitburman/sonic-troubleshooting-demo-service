# Phase 10 Runbook — sonic-buildimage Compatibility

## Files added

```
setup.py                                          ← SONiC build convention
setup.cfg                                         ← Static metadata
rules/sonic-troubleshooting-demo-service.mk       ← Ready-to-use rule template
```

## Test 1: Metadata consistency (runs anywhere)

```bash
source .venv/bin/activate
python3 -c "
import tomllib, configparser

with open('pyproject.toml', 'rb') as f:
    pp = tomllib.load(f)
cfg = configparser.ConfigParser()
cfg.read('setup.cfg')

assert pp['project']['name'] == cfg['metadata']['name']
assert pp['project']['version'] == cfg['metadata']['version']
print(f'✓ pyproject.toml == setup.cfg: {pp[\"project\"][\"name\"]} {pp[\"project\"][\"version\"]}')
"
```

## Test 2: Build wheel (runs anywhere)

```bash
source .venv/bin/activate
pip wheel . -w /tmp/sonic-wheel-test
ls -la /tmp/sonic-wheel-test/sonic_troubleshooting_demo_service-0.1.0-py3-none-any.whl
```

Expected: Wheel file exists with name matching the `.mk` file template.

## Test 3: pip install still works

```bash
source .venv/bin/activate
pip install -e .
sonic-troubleshooting-demo-service --help
```

## Test 4: Verify setup.py is parseable

```bash
python3 -c "exec(open('setup.py').read())" 2>&1 | head -1
# Should show setup() output, not a traceback
```

## Test 5: Integration into sonic-buildimage (on build machine)

```bash
# 1. Clone sonic-buildimage (separate directory)
cd /path/to/sonic-buildimage

# 2. Copy our repo into the src tree
cp -r /path/to/sonic-troubleshooting-demo-service src/

# 3. Copy the rule file
cp src/sonic-troubleshooting-demo-service/rules/sonic-troubleshooting-demo-service.mk rules/

# 4. Build the wheel
make target/python-wheels/bullseye/sonic_troubleshooting_demo_service-0.1.0-py3-none-any.whl
```

## Test 6: .mk file validation

```bash
# Check .mk file syntax (requires make)
make -f rules/sonic-troubleshooting-demo-service.mk -n 2>&1 | head -5
# Should print make commands, not syntax errors
```

## Phase 10 checklist

- [ ] `setup.py` exists and is valid Python
- [ ] `setup.cfg` exists with metadata matching `pyproject.toml`
- [ ] `rules/sonic-troubleshooting-demo-service.mk` follows sonic-buildimage conventions
- [ ] Wheel builds successfully: `pip wheel .` produces `sonic_troubleshooting_demo_service-0.1.0-py3-none-any.whl`
- [ ] `pip install -e .` still works (no regression)
- [ ] CLI commands still work (no regression)
- [ ] `.mk` file uses `SONIC_PYTHON_WHEELS` target
- [ ] `.mk` file references correct `_SRC_PATH`, `_PYTHON_VERSION`, `_NAME`, `_VERSION`
