"""Dynamic database configuration loader for SONiC Redis databases.

Reads database_config.json or falls back to db_constants.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from .db_constants import DEFAULT_DATABASE_CONFIG_PATHS, FALLBACK_DATABASES


@dataclass
class DbEntry:
    """Represents a single SONiC database entry."""

    id: int
    separator: str
    instance: str


@dataclass
class SonicDbConfig:
    """Loaded database configuration with metadata about its source."""

    databases: dict[str, DbEntry]
    raw_config: dict[str, Any]
    source: str
    used_fallback: bool
    errors: list[str] = field(default_factory=list)


class SonicDbConfigLoader:
    """Loads SONiC database configuration from JSON file or fallback."""

    def __init__(self, config_paths: list[str] | None = None) -> None:
        self._config_paths = config_paths or DEFAULT_DATABASE_CONFIG_PATHS
        self._errors: list[str] = []

    def load(self) -> SonicDbConfig:
        """Load database configuration.

        Tries each path in config_paths. Returns fallback if all fail.
        Never crashes on malformed config — collects errors instead.
        """
        for path in self._config_paths:
            if os.path.isfile(path):
                try:
                    return self._load_from_file(path)
                except (json.JSONDecodeError, OSError) as exc:
                    self._errors.append(f"Error reading {path}: {exc}")
                    continue

        # All paths failed — use fallback
        return self._build_fallback()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_from_file(self, path: str) -> SonicDbConfig:
        with open(path, "r") as fh:
            raw = json.load(fh)

        databases_block = raw.get("DATABASES")
        if not databases_block:
            self._errors.append(f"No 'DATABASES' key in {path}")
            return self._build_fallback()

        databases: dict[str, DbEntry] = {}
        for db_name, db_data in databases_block.items():
            db_id = db_data.get("id")
            if db_id is None:
                self._errors.append(
                    f"Missing 'id' for database '{db_name}' in {path}"
                )
                continue
            databases[db_name] = DbEntry(
                id=int(db_id),
                separator=db_data.get("separator", ":"),
                instance=db_data.get("instance", "redis"),
            )

        return SonicDbConfig(
            databases=databases,
            raw_config=raw,
            source=path,
            used_fallback=False,
            errors=list(self._errors),
        )

    def _build_fallback(self) -> SonicDbConfig:
        databases: dict[str, DbEntry] = {}
        for db_name, db_data in FALLBACK_DATABASES.items():
            databases[db_name] = DbEntry(
                id=db_data["id"],
                separator=db_data.get("separator", ":"),
                instance=db_data.get("instance", "redis"),
            )

        self._errors.append(
            "All config paths failed; using compiled-in fallback"
        )
        return SonicDbConfig(
            databases=databases,
            raw_config={},
            source="fallback",
            used_fallback=True,
            errors=list(self._errors),
        )
