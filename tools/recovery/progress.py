#!/usr/bin/env python3
"""Project an R1 receipt and writer progress into a read-only status snapshot."""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Optional


OPERATIONS = ("install", "restore", "collect", "reboot")
LINK_STATES = ("unobserved", "connected", "disconnected")
NUMBER = r"(0|[1-9][0-9]{0,8})"
PARTITION = r"(System|Data)"
SOURCE = re.compile(rf"D9W: source verified {NUMBER}/{NUMBER}")
SOURCES_START = re.compile(rf"D9W: checking all {NUMBER} source files before writing")
WRITTEN = re.compile(
    rf"D9W: written {PARTITION} {NUMBER}/{NUMBER} MiB \(part {NUMBER}/{NUMBER}\)"
)
ZEROED = re.compile(rf"D9W: zeroed Data through {NUMBER} MiB")
READBACK_START = re.compile(rf"D9W: verifying full {PARTITION} readback")
READBACK = re.compile(rf"D9W: readback {PARTITION} {NUMBER}/{NUMBER} MiB")
STAGES = (
    ("preflight", None),
    ("verify_source", None),
    ("write_partition", "system"),
    ("write_partition", "data"),
    ("verify_partition", "system"),
    ("verify_partition", "data"),
)


def operation_from(receipt):
    operations = receipt.get("operations")
    if (not isinstance(operations, list) or len(operations) != 1
            or operations[0] not in OPERATIONS):
        raise ValueError("expected a receipt for one recovery operation")
    return operations[0]


def receipt_state(receipt, operation, link):
    """Only the host's validated frames can establish a terminal state."""
    attempted = receipt.get("run_attempted") is True
    started = attempted and receipt.get("start_confirmed") is True
    outcome = receipt.get("outcome")
    code = receipt.get("returncode")
    has_code = type(code) is int and 0 <= code <= 255
    plan = receipt.get("plans", {}).get(operation, {}).get("state")
    if started and has_code:
        if (operation == "reboot" and outcome == "reboot_requested" and code == 0
                and receipt.get("request_verified") is True):
            return "reboot_requested"
        if (operation != "reboot" and outcome == "verified" and code == 0
                and receipt.get("verified") is True):
            return "verified"
        if outcome == "failed" and receipt.get("verified") is False:
            return "failed"
    if not started and (outcome == "blocked" or (not attempted and plan == "BLOCKED")):
        return "blocked"
    if attempted:
        if link != "connected" or receipt.get("error") is not None or outcome != "unknown":
            return "unknown"
        return "running" if started else "awaiting_start"
    if outcome == "not_started" or receipt.get("error") is not None:
        return "not_started"
    return "ready" if plan == "READY" else "waiting"


@dataclass(frozen=True)
class Counter:
    completed: int
    total: Optional[int]
    unit: str

    def __post_init__(self):
        if self.total is not None and not 0 <= self.completed <= self.total:
            raise ValueError("progress count exceeds its total")
        if self.total == 0:
            raise ValueError("progress total must be positive")

    def as_dict(self):
        return {"completed": self.completed, "total": self.total, "unit": self.unit}


class OperationProgress:
    """Keep the latest observation for a single R1 operation."""

    def __init__(self, operation):
        if operation not in OPERATIONS:
            raise ValueError("unsupported recovery operation")
        self.operation = operation
        self.stage = STAGES[0]
        self.counter = None
        self.partition_totals = {}

    def _advance(self, stage, counter):
        if STAGES.index(stage) < STAGES.index(self.stage):
            return
        phase, partition = stage
        if counter is not None and partition is not None:
            known_total = self.partition_totals.get(partition)
            if known_total is not None:
                if counter.total not in (None, known_total) or counter.completed > known_total:
                    return
                counter = Counter(counter.completed, known_total, counter.unit)
        if stage == self.stage and self.counter is not None:
            current = self.counter
            if (counter is None or counter.completed < current.completed
                    or (current.total is not None and counter.total != current.total)):
                return
        if counter is not None and partition is not None and counter.total is not None:
            self.partition_totals[partition] = counter.total
        self.stage, self.counter = (phase, partition), counter

    def observe(self, line):
        """Use only recognized writer counters, never free text or success markers."""
        if self.operation not in ("install", "restore") or len(line) > 1024:
            return
        line = line.rstrip("\r\n")
        try:
            if line == "D9W: checking AOSP System and clean Data before writing":
                self._advance(("verify_source", None), None)
            elif match := SOURCES_START.fullmatch(line):
                self._advance(("verify_source", None), Counter(0, int(match[1]), "items"))
            elif match := SOURCE.fullmatch(line):
                self._advance(("verify_source", None), Counter(int(match[1]), int(match[2]), "items"))
            elif match := WRITTEN.fullmatch(line):
                if 1 <= int(match[4]) <= int(match[5]):
                    self._advance(("write_partition", match[1].lower()),
                                  Counter(int(match[2]), int(match[3]), "MiB"))
            elif match := ZEROED.fullmatch(line):
                self._advance(("write_partition", "data"), Counter(int(match[1]), None, "MiB"))
            elif match := READBACK_START.fullmatch(line):
                self._advance(("verify_partition", match[1].lower()), Counter(0, None, "MiB"))
            elif match := READBACK.fullmatch(line):
                self._advance(("verify_partition", match[1].lower()),
                              Counter(int(match[2]), int(match[3]), "MiB"))
        except ValueError:
            # Invalid writer counters do not replace the last observation.
            return

    def snapshot(self, receipt, *, link="unobserved"):
        if operation_from(receipt) != self.operation:
            raise ValueError("receipt belongs to a different operation")
        if link not in LINK_STATES:
            raise ValueError("unsupported link observation")
        started = receipt.get("run_attempted") is True and receipt.get("start_confirmed") is True
        phase, partition = self.stage if started else (None, None)
        counter = self.counter if started else None
        if started and self.operation in ("collect", "reboot"):
            phase = self.operation
        return {
            "version": 1,
            "operation": self.operation,
            "state": receipt_state(receipt, self.operation, link),
            "phase": phase,
            "partition": partition,
            "progress": counter.as_dict() if counter is not None else None,
            "link": link,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_directory", type=Path, help="R1 host output directory")
    args = parser.parse_args()
    try:
        receipt = json.loads((args.run_directory / "uart-receipt.json").read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            raise ValueError("expected a JSON object receipt")
        progress = OperationProgress(operation_from(receipt))
        log = args.run_directory / "progress.log"
        if log.exists():
            with log.open(encoding="utf-8") as lines:
                for line in lines:
                    progress.observe(line)
        print(json.dumps(progress.snapshot(receipt), indent=2))
    except (AttributeError, OSError, ValueError) as error:
        sys.exit(f"recovery progress: {error}")


if __name__ == "__main__":
    main()
