import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.recovery.progress import OperationProgress


def receipt(operation="install", **changes):
    return {
        "operations": [operation],
        "plans": {operation: {"state": "READY", "reason": "available"}},
        "run_attempted": True,
        "start_confirmed": True,
        "outcome": "unknown",
        "verified": False,
        **changes,
    }


class RecoveryProgressTests(unittest.TestCase):
    def test_source_items_and_partition_progress(self):
        tracker = OperationProgress("install")
        tracker.observe("D9W: checking AOSP System and clean Data before writing")
        source = tracker.snapshot(receipt(), link="connected")
        self.assertEqual(source["phase"], "verify_source")
        self.assertIsNone(source["progress"])

        tracker.observe("D9W: source verified 4/12")
        source = tracker.snapshot(receipt(), link="connected")
        self.assertEqual(source["progress"], {"completed": 4, "total": 12, "unit": "items"})

        tracker.observe("D9W: written System 32/32 MiB (part 1/12)")
        tracker.observe("D9W: written Data 16/96 MiB (part 5/12)")
        tracker.observe("D9W: zeroed Data through 32 MiB")
        writing = tracker.snapshot(receipt(), link="connected")
        self.assertEqual(writing["partition"], "data")
        self.assertEqual(writing["progress"], {"completed": 32, "total": 96, "unit": "MiB"})

    def test_restore_does_not_invent_a_partition_total(self):
        tracker = OperationProgress("restore")
        tracker.observe("D9W: checking all 9 source files before writing")
        source = tracker.snapshot(receipt("restore"))
        self.assertEqual(source["progress"], {"completed": 0, "total": 9, "unit": "items"})
        tracker.observe("D9W: verifying full Data readback")
        readback = tracker.snapshot(receipt("restore"))
        self.assertIsNone(readback["progress"]["total"])
        tracker.observe("D9W: readback Data 32/96 MiB")
        self.assertEqual(tracker.snapshot(receipt("restore"))["progress"]["total"], 96)

    def test_stale_and_invalid_counters_do_not_replace_the_last(self):
        tracker = OperationProgress("install")
        tracker.observe("D9W: zeroed Data through 32 MiB")
        tracker.observe("D9W: written Data 16/28 MiB (part 5/12)")
        tracker.observe("D9W: written Data 48/96 MiB (part 7/12)")
        tracker.observe("D9W: written Data 128/96 MiB (part 8/12)")
        tracker.observe("D9W: written Data 56/128 MiB (part 9/12)")
        tracker.observe("D9W: written Data 56/96 MiB (part 0/12)")
        tracker.observe("D9W: source verified 12/12")
        observed = tracker.snapshot(receipt())
        self.assertEqual(observed["progress"], {"completed": 48, "total": 96, "unit": "MiB"})
        self.assertEqual(observed["phase"], "write_partition")

    def test_repeated_readback_header_preserves_progress(self):
        tracker = OperationProgress("restore")
        tracker.observe("D9W: readback Data 32/96 MiB")
        tracker.observe("D9W: verifying full Data readback")
        self.assertEqual(tracker.snapshot(receipt("restore"))["progress"]["completed"], 32)

    def test_only_receipt_establishes_verified_or_failed(self):
        tracker = OperationProgress("install")
        tracker.observe("D9W: readback Data 4096/4096 MiB")
        tracker.observe("D9W: AOSP SYSTEM AND DATA VERIFIED (synthetic)")
        self.assertEqual(tracker.snapshot(receipt(), link="connected")["state"], "running")

        success = receipt(outcome="verified", verified=True, returncode=0)
        self.assertEqual(tracker.snapshot(success)["state"], "verified")
        self.assertEqual(tracker.snapshot({**success, "returncode": False})["state"], "unknown")
        self.assertEqual(tracker.snapshot({**success, "start_confirmed": False})["state"], "unknown")

        tracker.observe("D9W: STOP synthetic reason; stay in TWRP")
        self.assertEqual(tracker.snapshot(receipt(), link="connected")["state"], "running")
        failure = receipt(outcome="failed", returncode=1)
        self.assertEqual(tracker.snapshot(failure, link="disconnected")["state"], "failed")

    def test_lost_or_stale_link_keeps_last_progress_without_claiming_running(self):
        tracker = OperationProgress("install")
        tracker.observe("D9W: readback Data 32/96 MiB")
        current = tracker.snapshot(receipt(), link="connected")
        self.assertEqual(current["state"], "running")
        for snapshot in (
            tracker.snapshot(receipt(), link="disconnected"),
            tracker.snapshot(receipt()),
            tracker.snapshot(receipt(error="link timeout"), link="connected"),
        ):
            self.assertEqual(snapshot["state"], "unknown")
            self.assertEqual(snapshot["phase"], current["phase"])
            self.assertEqual(snapshot["progress"], current["progress"])

    def test_plan_and_run_acknowledgement_are_distinct(self):
        tracker = OperationProgress("install")
        planned = receipt(run_attempted=False, start_confirmed=False, outcome="planned")
        self.assertEqual(tracker.snapshot(planned)["state"], "ready")
        blocked = {**planned, "plans": {"install": {"state": "BLOCKED"}}}
        self.assertEqual(tracker.snapshot(blocked)["state"], "blocked")
        pending = receipt(start_confirmed=False)
        self.assertEqual(tracker.snapshot(pending, link="connected")["state"], "awaiting_start")
        self.assertEqual(tracker.snapshot(pending)["state"], "unknown")
        self.assertIsNone(tracker.snapshot(pending)["phase"])

    def test_reboot_acknowledgement_does_not_infer_boot(self):
        tracker = OperationProgress("reboot")
        tracker.observe("D9W: REBOOT REQUESTED")
        self.assertEqual(tracker.snapshot(receipt("reboot"), link="connected")["state"], "running")
        ack = receipt("reboot", outcome="reboot_requested", request_verified=True, returncode=0)
        result = tracker.snapshot(ack)
        self.assertEqual(result["state"], "reboot_requested")
        self.assertEqual(result["phase"], "reboot")
        self.assertNotIn("reboot_observed", result)

    def test_cli_projects_local_receipt_without_echoing_private_fields(self):
        script = Path(__file__).resolve().parents[1] / "tools/recovery/progress.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "uart-receipt.json").write_text(json.dumps(receipt(helper_nonce="private-example")))
            (path / "progress.log").write_text("D9W: readback System 512/1024 MiB\n")
            result = subprocess.run([sys.executable, "-B", script, path], check=True, capture_output=True)
        self.assertNotIn(b"private-example", result.stdout)
        self.assertEqual(json.loads(result.stdout), {
            "version": 1,
            "operation": "install",
            "state": "unknown",
            "phase": "verify_partition",
            "partition": "system",
            "progress": {"completed": 512, "total": 1024, "unit": "MiB"},
            "link": "unobserved",
        })


if __name__ == "__main__":
    unittest.main()
