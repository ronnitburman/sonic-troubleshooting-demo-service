# Phase 2 Runbook — Database Configuration

## How to test the DB config loader

### Test 1: Fallback loading (no JSON file)

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.db_config_loader import SonicDbConfigLoader

config = SonicDbConfigLoader().load()
print('Source:', config.source)
print('Used fallback:', config.used_fallback)
print('Errors:', config.errors)
print()
for name, db in sorted(config.databases.items()):
    print(f'  {name}: id={db.id}, sep={repr(db.separator)}, instance={db.instance}')
"
```

Expected output (on dev machine — no SONiC JSON file):
```
Source: fallback
Used fallback: True
Errors: ['All config paths failed; using compiled-in fallback']

  APPL_DB: id=0, sep=':', instance=redis
  ASIC_DB: id=1, sep=':', instance=redis
  CONFIG_DB: id=4, sep='|', instance=redis
  COUNTERS_DB: id=2, sep=':', instance=redis
  STATE_DB: id=6, sep=':', instance=redis
```

### Test 2: Key assertions

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.db_config_loader import SonicDbConfigLoader
db = SonicDbConfigLoader().load().databases
assert db['CONFIG_DB'].separator == '|', 'FAIL: CONFIG_DB sep'
assert db['CONFIG_DB'].id == 4, 'FAIL: CONFIG_DB id'
assert db['APPL_DB'].separator == ':', 'FAIL: APPL_DB sep'
assert db['STATE_DB'].id == 6, 'FAIL: STATE_DB id'
print('All assertions passed')
"
```

### Test 3: Loading from a real JSON file (SONiC VS only)

If you have a SONiC VS with `/var/run/redis/sonic-db/database_config.json`:

```bash
# On SONiC VS:
python3 -c "
from sonic_troubleshooting_demo_service.db_config_loader import SonicDbConfigLoader
config = SonicDbConfigLoader().load()
print('Source:', config.source)
print('Used fallback:', config.used_fallback)
print('Errors:', config.errors)
print('Number of databases loaded:', len(config.databases))
"
```

Expected: `used_fallback=False`, `source` points to the JSON file, no fallback error in `errors`.

### Test 4: Graceful handling of malformed JSON (unit test style)

```bash
source .venv/bin/activate
python3 -c "
import json, os, tempfile
from sonic_troubleshooting_demo_service.db_config_loader import SonicDbConfigLoader

# Create a malformed JSON file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    f.write('{not valid json')
    bad_path = f.name

# Create a valid JSON file without DATABASES key
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump({'SOME_OTHER_KEY': 'value'}, f)
    no_db_path = f.name

# Test malformed JSON → falls back
config = SonicDbConfigLoader([bad_path]).load()
print('Malformed JSON handled:', config.used_fallback)
assert config.used_fallback

# Test missing DATABASES key → falls back
config = SonicDbConfigLoader([no_db_path]).load()
print('Missing DATABASES key handled:', config.used_fallback)
assert config.used_fallback

os.unlink(bad_path)
os.unlink(no_db_path)
print('✓ Edge cases handled correctly')
"
```

## Phase 2 checklist

- [ ] `db_constants.py` has 5 DBs with correct IDs and separators
- [ ] `db_config_loader.py` compiles and imports
- [ ] Fallback returns all 5 DBs with `used_fallback=True`
- [ ] CONFIG_DB separator is `|` (not `:`)
- [ ] Errors list includes fallback message when no file found
- [ ] Malformed JSON doesn't crash — falls back gracefully
- [ ] Missing `DATABASES` key doesn't crash — falls back gracefully
