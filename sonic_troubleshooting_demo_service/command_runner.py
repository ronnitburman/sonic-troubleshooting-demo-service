"""Safe subprocess command execution for SONiC CLI commands."""

from __future__ import annotations

import logging
import shutil
import subprocess

logger = logging.getLogger(__name__)


def command_exists(command: str) -> bool:
    """Return True if *command* is found on PATH."""
    return shutil.which(command) is not None


def run_command(args: list[str]) -> str:
    """Run a command via subprocess and return its stdout.

    Raises RuntimeError if the command exits with a non-zero code.

    Safety guarantees:
    - No shell=True — args are passed directly to exec.
    - capture_output=True — no output leaks to the terminal.
    - text=True — returns str, not bytes.
    """
    logger.info("Running command: %s", " ".join(args))
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit {result.returncode}): "
            f"{' '.join(args)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.stdout.strip()
