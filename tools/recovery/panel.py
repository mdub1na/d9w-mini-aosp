#!/usr/bin/env python3
"""Map a status snapshot to display-only variables for a TWRP page."""

import argparse
import json
from pathlib import Path
import sys


OPERATION_LABELS = {
    "install": "Install AOSP",
    "restore": "Restore stock",
    "collect": "Collect logs",
    "reboot": "Reboot",
}
STATUS_LABELS = {
    "waiting": "Waiting for recovery",
    "ready": "Ready",
    "blocked": "Preflight blocked",
    "not_started": "Operation not started",
    "awaiting_start": "Waiting for device start",
    "running": "In progress",
    "unknown": "Result unknown",
    "verified": "Verified",
    "failed": "Failed",
    "reboot_requested": "Reboot requested",
}
LINK_LABELS = {
    "unobserved": "Link unobserved",
    "connected": "Host connected",
    "disconnected": "Host disconnected",
}
PHASE_LABELS = {
    (None, None): "",
    ("preflight", None): "Checking prerequisites",
    ("verify_source", None): "Verifying source data",
    ("write_partition", "system"): "Writing System",
    ("write_partition", "data"): "Writing Data",
    ("verify_partition", "system"): "Verifying System readback",
    ("verify_partition", "data"): "Verifying Data readback",
    ("collect", None): "Collecting logs",
    ("reboot", None): "Normal boot request",
}
MAX_COUNTER = 999_999_999


def counter_text(progress, running):
    """Return the measurement label and an optional bounded percentage."""
    if progress is None:
        return "", None
    if not isinstance(progress, dict):
        raise ValueError("progress must be an object or null")
    completed = progress.get("completed")
    total = progress.get("total")
    unit = progress.get("unit")
    if (type(completed) is not int or not 0 <= completed <= MAX_COUNTER
            or (total is not None and (type(total) is not int
                                       or not max(1, completed) <= total <= MAX_COUNTER))
            or unit not in ("items", "MiB")):
        raise ValueError("invalid panel progress counter")
    amount = f"{completed:,}" if total is None else f"{completed:,} / {total:,}"
    label = f"{amount} {unit}"
    if not running:
        return f"Last reported {label}", None
    percent = completed * 100 // total if total is not None else None
    return label, percent


def panel_variables(snapshot):
    """Project a version-1 snapshot into bounded strings for DataManager."""
    if (not isinstance(snapshot, dict) or type(snapshot.get("version")) is not int
            or snapshot["version"] != 1):
        raise ValueError("expected a version-1 operation status snapshot")
    try:
        operation = OPERATION_LABELS[snapshot["operation"]]
        state = snapshot["state"]
        status = STATUS_LABELS[state]
        phase = PHASE_LABELS[snapshot["phase"], snapshot["partition"]]
        link = LINK_LABELS[snapshot["link"]]
        progress = snapshot["progress"]
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid panel operation, state, phase, partition or link") from exc
    label, percent = counter_text(progress, state == "running")
    return {
        "d9w_panel_operation": operation,
        "d9w_panel_status": status,
        "d9w_panel_phase": phase,
        "d9w_panel_counter": label,
        "d9w_panel_show_bar": "1" if percent is not None else "0",
        "d9w_panel_percent": str(percent if percent is not None else 0),
        "d9w_panel_link": link,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="version-1 operation status JSON file")
    args = parser.parse_args()
    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        print(json.dumps(panel_variables(snapshot), indent=2))
    except (OSError, ValueError) as exc:
        sys.exit(f"recovery panel: {exc}")


if __name__ == "__main__":
    main()
