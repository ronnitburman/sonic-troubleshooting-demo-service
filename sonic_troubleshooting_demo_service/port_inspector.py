"""SONiC port state inspection across multiple databases."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .redis_client import SonicRedisClient

logger = logging.getLogger(__name__)


@dataclass
class PortView:
    """Aggregated view of a single port across SONiC databases."""

    port: str
    config_key: str
    config_db: dict[str, str]
    appl_db: dict[str, str]
    state_db: dict[str, str]


class PortInspector:
    """Inspects a SONiC port by reading CONFIG_DB, APPL_DB, and STATE_DB."""

    def __init__(
        self, redis_client: SonicRedisClient | None = None
    ) -> None:
        self._redis = redis_client or SonicRedisClient()

    def inspect(self, port: str) -> PortView:
        """Return a PortView with data from all available databases.

        Missing keys are acceptable — partial data is returned as
        empty dicts rather than throwing an exception.
        """
        config_key = f"PORT|{port}"

        # CONFIG_DB is the authoritative source for port config.
        config_db = self._safe_hgetall("CONFIG_DB", config_key)

        # APPL_DB uses ':' separator by convention.
        appl_db = self._safe_hgetall("APPL_DB", f"PORT_TABLE:{port}")

        # STATE_DB may use '|' or ':' — try both conservatively.
        state_db = self._safe_hgetall("STATE_DB", f"PORT_TABLE|{port}")
        if not state_db:
            state_db = self._safe_hgetall("STATE_DB", f"PORT_TABLE:{port}")

        return PortView(
            port=port,
            config_key=config_key,
            config_db=config_db,
            appl_db=appl_db,
            state_db=state_db,
        )

    def _safe_hgetall(self, db_name: str, key: str) -> dict[str, str]:
        """Return hgetall result, or {} on any failure."""
        try:
            return self._redis.hgetall(db_name, key)
        except Exception:
            logger.debug(
                "Could not read %s key %s", db_name, key, exc_info=True
            )
            return {}
