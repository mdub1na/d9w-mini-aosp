import os
from pathlib import Path
import subprocess
import tempfile
import unittest


NATIVE = Path(__file__).resolve().parents[1] / "tools" / "recovery" / "native"


class RecoveryNativeStatusTest(unittest.TestCase):
    def compile_and_run(self, name, sources):
        with tempfile.TemporaryDirectory() as temporary_directory:
            executable = Path(temporary_directory) / name
            subprocess.run(
                [os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra",
                 "-Werror", "-Wpedantic", *(str(NATIVE / source) for source in sources),
                 "-o", str(executable)],
                check=True,
            )
            subprocess.run([str(executable)], check=True)

    def test_snapshot_storage(self):
        self.compile_and_run(
            "test_operation_status", ["operation_status.c", "test_operation_status.c"]
        )

    def test_progress_parser(self):
        self.compile_and_run(
            "test_operation_monitor", ["operation_monitor.c", "test_operation_monitor.c"]
        )
