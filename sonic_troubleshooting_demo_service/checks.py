"""Troubleshooting checks for SONiC port state."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .port_inspector import PortView

logger = logging.getLogger(__name__)


@dataclass
class Finding:
    """A single troubleshooting finding with severity and evidence."""

    severity: str  # "error", "warning", or "info"
    code: str
    message: str
    evidence: dict[str, str] = field(default_factory=dict)


def run_port_checks(port_view: PortView) -> list[Finding]:
    """Run all port checks and return a list of Findings.

    Returns an empty list if no issues are found.
    """
    findings: list[Finding] = []
    cfg = port_view.config_db
    port = port_view.port

    # 1. CONFIG_PORT_KEY_MISSING — severity: error
    if not cfg:
        findings.append(
            Finding(
                severity="error",
                code="CONFIG_PORT_KEY_MISSING",
                message=f"No CONFIG_DB entry found for port {port}",
                evidence={"port": port},
            )
        )
        return findings  # Cannot run further checks without config data

    # 2. ADMIN_STATUS_MISSING — severity: error
    admin_status = cfg.get("admin_status")
    if admin_status is None:
        findings.append(
            Finding(
                severity="error",
                code="ADMIN_STATUS_MISSING",
                message=f"admin_status field missing for port {port}",
                evidence={"port": port},
            )
        )

    # 3. ADMIN_STATUS_INVALID — severity: error
    elif admin_status not in ("up", "down"):
        findings.append(
            Finding(
                severity="error",
                code="ADMIN_STATUS_INVALID",
                message=(
                    f"admin_status is '{admin_status}' for port {port} "
                    f"(expected 'up' or 'down')"
                ),
                evidence={
                    "port": port,
                    "admin_status": admin_status,
                },
            )
        )

    # 4. PORT_ADMIN_DOWN — severity: info
    elif admin_status == "down":
        findings.append(
            Finding(
                severity="info",
                code="PORT_ADMIN_DOWN",
                message=f"Port {port} is administratively down",
                evidence={
                    "port": port,
                    "admin_status": admin_status,
                },
            )
        )

    # 5. MTU_MISSING — severity: info (absent in CONFIG_DB means default)
    if "mtu" not in cfg:
        findings.append(
            Finding(
                severity="info",
                code="MTU_MISSING",
                message=f"MTU field missing for port {port}",
                evidence={"port": port},
            )
        )

    return findings
