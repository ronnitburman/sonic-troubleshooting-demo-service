"""CLI entry point for the SONiC troubleshooting demo service.

Commands: inspect, check, remediate.
"""

from __future__ import annotations

import logging
import sys

import typer
from rich.console import Console
from rich.table import Table

from .checks import Finding, run_port_checks
from .port_inspector import PortInspector
from .remediation import PortRemediationService

app = typer.Typer(
    name="sonic-troubleshooting-demo-service",
    help="SONiC troubleshooting demo service — inspect, check, remediate.",
)
console = Console()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# inspect
# ---------------------------------------------------------------------------

@app.command()
def inspect(port: str = typer.Option(..., help="Port name, e.g. Ethernet0")):
    """Inspect a SONiC port across CONFIG_DB, APPL_DB, and STATE_DB."""
    inspector = PortInspector()
    view = inspector.inspect(port)

    # Always print CONFIG_DB
    _print_db_table(f"CONFIG_DB — PORT|{port}", view.config_db)

    # Print APPL_DB and STATE_DB only when they have data
    if view.appl_db:
        _print_db_table(f"APPL_DB — PORT_TABLE:{port}", view.appl_db)
    if view.state_db:
        _print_db_table(f"STATE_DB — PORT_TABLE|{port}", view.state_db)


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

@app.command()
def check(port: str = typer.Option(..., help="Port name, e.g. Ethernet0")):
    """Run troubleshooting checks on a port."""
    inspector = PortInspector()
    view = inspector.inspect(port)
    findings = run_port_checks(view)

    if not findings:
        console.print(f"[green]✓ No issues found for port {port}[/green]")
        return

    # Group by severity
    by_severity: dict[str, list[Finding]] = {}
    for f in findings:
        by_severity.setdefault(f.severity, []).append(f)

    # Print in severity order
    for severity in ("error", "warning", "info"):
        group = by_severity.get(severity)
        if not group:
            continue
        color = {"error": "red", "warning": "yellow", "info": "blue"}.get(
            severity, "white"
        )
        console.print(f"\n[bold {color}]{severity.upper()}[/bold {color}]")
        for finding in group:
            console.print(f"  [{color}]{finding.code}[/{color}]")
            console.print(f"    {finding.message}")
            if finding.evidence:
                for k, v in finding.evidence.items():
                    console.print(f"    {k}: {v}")


# ---------------------------------------------------------------------------
# remediate
# ---------------------------------------------------------------------------

@app.command()
def remediate(
    port: str = typer.Option(..., help="Port name, e.g. Ethernet0"),
    target_status: str = typer.Option(
        "down", help="Target admin status: up or down"
    ),
    write_mode: str = typer.Option(
        "cli", help="Write mode: cli or redis"
    ),
    restore: bool = typer.Option(
        True, "--restore/--no-restore", help="Restore original status after hold"
    ),
    hold_seconds: int = typer.Option(
        5, help="Seconds to hold target status before restoring"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Inspect and check without changing anything"
    ),
):
    """Remediate a port: change admin status, verify, and optionally restore."""
    service = PortRemediationService()
    result = service.remediate(
        port=port,
        target_status=target_status,
        write_mode=write_mode,
        restore=restore,
        hold_seconds=hold_seconds,
        dry_run=dry_run,
    )

    # Summary table
    summary = Table(title=f"Remediation Result — {port}")
    summary.add_column("Field", style="cyan")
    summary.add_column("Value")
    summary.add_row("Port", result.port)
    summary.add_row("Original status", result.original_status or "N/A")
    summary.add_row("Target status", result.target_status)
    summary.add_row("Write mode", result.write_mode)
    summary.add_row("Restore", str(result.restored))
    summary.add_row("Final status", result.final_status or "N/A")
    summary.add_row("Success", "✓" if result.success else "✗")
    console.print(summary)

    # Messages
    if result.messages:
        console.print("\n[bold]Messages:[/bold]")
        for msg in result.messages:
            console.print(f"  • {msg}")

    # Findings before
    if result.findings_before:
        console.print("\n[bold yellow]Findings (before):[/bold yellow]")
        _print_findings_compact(result.findings_before)

    # Findings after
    if result.findings_after:
        console.print("\n[bold yellow]Findings (after):[/bold yellow]")
        _print_findings_compact(result.findings_after)

    sys.exit(0 if result.success else 1)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _print_db_table(title: str, data: dict[str, str]) -> None:
    """Print a single Rich table for a database view."""
    table = Table(title=title)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    for key, value in sorted(data.items()):
        table.add_row(key, value)
    console.print(table)


def _print_findings_compact(findings: list[Finding]) -> None:
    """Print findings in a compact one-line-per-finding format."""
    for f in findings:
        color = {"error": "red", "warning": "yellow", "info": "blue"}.get(
            f.severity, "white"
        )
        console.print(
            f"  [{color}]{f.severity.upper()}[/{color}] "
            f"{f.code}: {f.message}"
        )


# ---------------------------------------------------------------------------
# Entry point hook
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for console_scripts."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app()


if __name__ == "__main__":
    main()
