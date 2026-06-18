"""Fallback database constants for SONiC Redis databases.

These are used when /var/run/redis/sonic-db/database_config.json
is not available (e.g., outside a SONiC switch).
"""

FALLBACK_DATABASES = {
    "APPL_DB": {"id": 0, "separator": ":", "instance": "redis"},
    "ASIC_DB": {"id": 1, "separator": ":", "instance": "redis"},
    "COUNTERS_DB": {"id": 2, "separator": ":", "instance": "redis"},
    "CONFIG_DB": {"id": 4, "separator": "|", "instance": "redis"},
    "STATE_DB": {"id": 6, "separator": ":", "instance": "redis"},
}

DEFAULT_DATABASE_CONFIG_PATHS = [
    "/var/run/redis/sonic-db/database_config.json",
    "/etc/sonic/database_config.json",
]
