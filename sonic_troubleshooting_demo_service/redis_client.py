"""Redis client for SONiC Redis databases over Unix socket."""

from __future__ import annotations

import logging

import redis

from .db_config_loader import SonicDbConfig, SonicDbConfigLoader

REDIS_SOCKET = "/var/run/redis/redis.sock"

logger = logging.getLogger(__name__)


class SonicRedisClient:
    """Wraps redis.Redis for SONiC's multi-DB Redis setup.

    Each SONiC DB (CONFIG_DB, APPL_DB, etc.) is a separate Redis
    logical database reached via the same Unix socket.
    """

    def __init__(self, db_config: SonicDbConfig | None = None) -> None:
        self._db_config = db_config or SonicDbConfigLoader().load()
        # Cache Redis connections keyed by db_id to avoid repeated
        # connection setup.
        self._clients: dict[int, redis.Redis] = {}

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def _require_db(self, db_name: str) -> int:
        """Return db_id for *db_name*, raising KeyError if unknown."""
        if db_name not in self._db_config.databases:
            available = ", ".join(sorted(self._db_config.databases.keys()))
            raise KeyError(
                f"Unknown database: {db_name}. Available: {available}"
            )
        return self._db_config.databases[db_name].id

    def get_db_id(self, db_name: str) -> int:
        """Return the Redis logical DB number for *db_name*."""
        return self._require_db(db_name)

    def get_separator(self, db_name: str) -> str:
        """Return the separator character for *db_name*."""
        if db_name not in self._db_config.databases:
            available = ", ".join(sorted(self._db_config.databases.keys()))
            raise KeyError(
                f"Unknown database: {db_name}. Available: {available}"
            )
        return self._db_config.databases[db_name].separator

    def client_for_db(self, db_name: str) -> redis.Redis:
        """Return a redis.Redis instance connected to *db_name*."""
        db_id = self._require_db(db_name)
        if db_id not in self._clients:
            logger.debug("Connecting to Redis DB %d (%s)", db_id, db_name)
            self._clients[db_id] = redis.Redis(
                unix_socket_path=REDIS_SOCKET,
                db=db_id,
                decode_responses=True,
            )
        return self._clients[db_id]

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    def exists(self, db_name: str, key: str) -> bool:
        """Return True if *key* exists in *db_name*."""
        r = self.client_for_db(db_name)
        return bool(r.exists(key))

    def hgetall(self, db_name: str, key: str) -> dict[str, str]:
        """Return all fields/values of hash at *key* in *db_name*.

        Returns an empty dict if the key does not exist.
        """
        r = self.client_for_db(db_name)
        result = r.hgetall(key)
        return result or {}

    def hget(
        self, db_name: str, key: str, field: str
    ) -> str | None:
        """Return a single hash field value, or None if missing."""
        r = self.client_for_db(db_name)
        return r.hget(key, field)

    def key_type(self, db_name: str, key: str) -> str:
        """Return the Redis type name for *key* (e.g. 'hash', 'none')."""
        r = self.client_for_db(db_name)
        return r.type(key)

    def scan_keys(
        self, db_name: str, pattern: str, count: int = 100
    ) -> list[str]:
        """Scan keys in *db_name* matching *pattern*.

        Uses SCAN via scan_iter to avoid blocking the server.
        """
        r = self.client_for_db(db_name)
        keys: list[str] = []
        for key in r.scan_iter(match=pattern, count=count):
            keys.append(key)
        return keys

    # ------------------------------------------------------------------
    # Write method
    # ------------------------------------------------------------------

    def hset(
        self, db_name: str, key: str, field: str, value: str
    ) -> int:
        """Set a hash field. Returns the number of fields that were added."""
        r = self.client_for_db(db_name)
        return r.hset(key, field, value)
