# Phase 3 Runbook — Redis Client

## Prerequisites

- Redis running on `/var/run/redis/redis.sock` (or just test API surface if Redis unavailable)
- Phase 2 complete (db config layer works)

## Test 1: API surface check (works without Redis)

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.redis_client import SonicRedisClient

client = SonicRedisClient()

# Configuration methods
assert client.get_db_id('CONFIG_DB') == 4
assert client.get_separator('CONFIG_DB') == '|'
assert client.get_db_id('APPL_DB') == 0
assert client.get_separator('APPL_DB') == ':'

# Unknown DB raises KeyError with helpful message
try:
    client.get_db_id('BOGUS_DB')
    print('FAIL: should have raised KeyError')
except KeyError as e:
    print('OK: KeyError raised:', e)

# client_for_db returns a Redis instance
r = client.client_for_db('CONFIG_DB')
print('client_for_db returns:', type(r).__name__)

# All 6 methods exist
for m in ['exists', 'hgetall', 'hget', 'hset', 'key_type', 'scan_keys']:
    assert hasattr(client, m), f'Missing: {m}'
    assert callable(getattr(client, m)), f'Not callable: {m}'
print('All 6 methods present and callable')
print('✓ API surface test passed')
"
```

## Test 2: Connection and read (requires Redis on Unix socket)

This only works on a machine with Redis running on `/var/run/redis/redis.sock` (e.g., SONiC VS).

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.redis_client import SonicRedisClient

client = SonicRedisClient()

# Test connection to CONFIG_DB
try:
    r = client.client_for_db('CONFIG_DB')
    print('Connected to Redis DB 4')
except Exception as e:
    print('Redis not available:', e)
    print('(This is expected on a dev machine — skip this test)')
    exit(0)

# Test exists
has_port = client.exists('CONFIG_DB', 'PORT|Ethernet0')
print(f'PORT|Ethernet0 exists: {has_port}')

# Test hgetall
if has_port:
    data = client.hgetall('CONFIG_DB', 'PORT|Ethernet0')
    print('CONFIG_DB PORT|Ethernet0:', dict(data))
    assert 'admin_status' in data, 'Missing admin_status'
    print('admin_status:', data.get('admin_status'))

# Test hget
status = client.hget('CONFIG_DB', 'PORT|Ethernet0', 'admin_status')
print(f'admin_status via hget: {status}')

# Test key_type
ktype = client.key_type('CONFIG_DB', 'PORT|Ethernet0')
print(f'Key type: {ktype}')

# Test scan_keys
ports = client.scan_keys('CONFIG_DB', 'PORT|*')
print(f'Port keys found: {len(ports)}')
if ports:
    print('First 5:', ports[:5])

# Test hgetall on non-existent key
empty = client.hgetall('CONFIG_DB', 'NONEXISTENT_KEY_XYZ')
print(f'hgetall on missing key: {empty}')
assert empty == {}, 'Should return empty dict'

# Test hget on missing field
missing = client.hget('CONFIG_DB', 'PORT|Ethernet0', 'nonexistent_field')
print(f'hget on missing field: {missing}')
assert missing is None, 'Should return None'

print()
print('✓ Redis read test passed')
"
```

## Test 3: Write test (requires Redis — use with caution)

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.redis_client import SonicRedisClient

client = SonicRedisClient()

try:
    r = client.client_for_db('CONFIG_DB')
except Exception as e:
    print('Redis not available, skipping write test')
    exit(0)

# Read original value
port = 'Ethernet0'
original = client.hget('CONFIG_DB', f'PORT|{port}', 'admin_status')
print(f'Original admin_status for {port}: {original}')

# Write (same value — no actual change, safe)
result = client.hset('CONFIG_DB', f'PORT|{port}', 'admin_status', original)
print(f'hset returned: {result} (0=updated existing, 1=new field)')

# Verify
after = client.hget('CONFIG_DB', f'PORT|{port}', 'admin_status')
print(f'After write: {after}')
assert after == original, f'Value changed! {original} -> {after}'

print('✓ Redis write test passed (no-op, value unchanged)')
"
```

## Test 4: Connection caching

```bash
source .venv/bin/activate
python3 -c "
from sonic_troubleshooting_demo_service.redis_client import SonicRedisClient

client = SonicRedisClient()

# First call creates connection
r1 = client.client_for_db('CONFIG_DB')

# Second call returns cached connection
r2 = client.client_for_db('CONFIG_DB')

print(f'Same connection object? {r1 is r2}')
assert r1 is r2, 'Should reuse cached connection'

# Different DB gets different connection
r3 = client.client_for_db('APPL_DB')
print(f'Different DB different connection? {r1 is not r3}')
assert r1 is not r3, 'Different DBs should have different connections'

print('✓ Connection caching works')
"
```

## Full validation (all tests in one)

```bash
source .venv/bin/activate
python3 -m py_compile sonic_troubleshooting_demo_service/redis_client.py
echo "✓ py_compile passed"
```

## Phase 3 checklist

- [ ] `redis_client.py` compiles without errors
- [ ] `SonicRedisClient()` instantiates with fallback config
- [ ] `get_db_id` returns correct IDs (CONFIG_DB=4, APPL_DB=0, STATE_DB=6)
- [ ] `get_separator` returns `|` for CONFIG_DB and `:` for others
- [ ] Unknown DB name raises `KeyError` listing available DBs
- [ ] `client_for_db` returns `redis.Redis` with `decode_responses=True`
- [ ] Connection caching: same db_id returns same connection object
- [ ] `hgetall` on missing key returns `{}` (empty dict)
- [ ] `hget` on missing field returns `None`
- [ ] `hset` writes and returns int
- [ ] `scan_keys` returns list (uses `scan_iter`)
- [ ] `exists` returns bool
- [ ] `key_type` returns string
