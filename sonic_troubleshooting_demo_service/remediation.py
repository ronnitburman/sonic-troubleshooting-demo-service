"""Port remediation logic — toggle admin state and restore."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from .checks import Finding, run_port_checks
from .command_runner import command_exists, run_command
from .port_inspector import PortInspector, PortView
from .redis_client import SonicRedisClient

logger = logging.getLogger(__name__)


@dataclass
class RemediationResult:
    """Full result of a remediation attempt."""

    port: str
    original_status: str | None
    target_status: str
    final_status: str | None
    write_mode: str
    restored: bool
    success: bool
    messages: list[str] = field(default_factory=list)
    findings_before: list[Finding] = field(default_factory=list)
    findings_after: list[Finding] = field(default_factory=list)


class PortRemediationService:
    """Applies and optionally restores port admin status."""

    def __init__(
        self,
        redis_client: SonicRedisClient | None = None,
        inspector: PortInspector | None = None,
    ) -> None:
        self._redis = redis_client or SonicRedisClient()
        self._inspector = inspector or PortInspector(self._redis)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def remediate(
        self,
        port: str,
        target_status: str = "down",
        write_mode: str = "cli",
        restore: bool = True,
        hold_seconds: int = 5,
        dry_run: bool = False,
    ) -> RemediationResult:
        """Apply target admin status and optionally restore original.

        Args:
            port: Port name (e.g. "Ethernet0").
            target_status: "up" or "down".
            write_mode: "cli" (config command) or "redis" (direct write).
            restore: If True, restore original status after hold.
            hold_seconds: Seconds to hold the target status.
            dry_run: If True, inspect and check but do not change anything.
        """
        self._validate_inputs(target_status, write_mode)

        # 1. Inspect the port
        port_view = self._inspector.inspect(port)
        original_status = port_view.config_db.get("admin_status")

        # 2. Run checks before remediation
        findings_before = run_port_checks(port_view)

        # 3. Dry-run path — skips all side effects
        if dry_run:
            return RemediationResult(
                port=port,
                original_status=original_status,
                target_status=target_status,
                final_status=original_status,
                write_mode=write_mode,
                restored=False,
                success=True,
                messages=["[DRY RUN] No changes applied."],
                findings_before=findings_before,
                findings_after=[],
            )

        if write_mode == "cli" and not command_exists("config"):
            raise RuntimeError(
                "CLI write mode requires the 'config' command on PATH"
            )

        result = RemediationResult(
            port=port,
            original_status=original_status,
            target_status=target_status,
            final_status=None,
            write_mode=write_mode,
            restored=False,
            success=False,
            findings_before=findings_before,
        )

        try:
            # 4. Apply target status
            self._apply_status(port, target_status, write_mode)
            result.messages.append(
                f"Applied admin_status={target_status} to {port} "
                f"via {write_mode}"
            )

            # 5. Verify
            verified = self._read_current_status(port)
            result.final_status = verified
            result.messages.append(
                f"Verified admin_status={verified} for {port}"
            )

            # 6. Hold
            time.sleep(hold_seconds)

            # 7. Restore original status
            if restore:
                restore_to = original_status or "up"
                if original_status is None:
                    result.messages.append(
                        "WARNING: original status was missing; "
                        f"restoring to '{restore_to}'"
                    )

                self._apply_status(port, restore_to, write_mode)
                result.restored = True
                result.messages.append(
                    f"Restored admin_status={restore_to} to {port}"
                )

                # Verify restoration
                final_verified = self._read_current_status(port)
                result.final_status = final_verified
                result.messages.append(
                    f"Final verified admin_status={final_verified} for {port}"
                )

            # 8. Run checks after remediation
            result.findings_after = run_port_checks(
                self._inspector.inspect(port)
            )

            result.success = True

        except Exception as exc:
            result.messages.append(f"ERROR: {exc}")
            result.success = False

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_inputs(target_status: str, write_mode: str) -> None:
        if target_status not in ("up", "down"):
            raise ValueError(
                f"target_status must be 'up' or 'down', got '{target_status}'"
            )
        if write_mode not in ("cli", "redis"):
            raise ValueError(
                f"write_mode must be 'cli' or 'redis', got '{write_mode}'"
            )

    def _apply_status(
        self, port: str, status: str, write_mode: str
    ) -> None:
        if write_mode == "cli":
            self._apply_via_cli(port, status)
        else:
            self._apply_via_redis(port, status)

    def _apply_via_cli(self, port: str, status: str) -> None:
        if status == "down":
            args = ["config", "interface", "shutdown", port]
        else:
            args = ["config", "interface", "startup", port]
        run_command(args)

    def _apply_via_redis(self, port: str, status: str) -> None:
        self._redis.hset(
            "CONFIG_DB", f"PORT|{port}", "admin_status", status
        )

    def _read_current_status(self, port: str) -> str | None:
        return self._redis.hget("CONFIG_DB", f"PORT|{port}", "admin_status")
