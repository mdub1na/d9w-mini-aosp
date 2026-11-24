import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET


RECOVERY = Path(__file__).resolve().parents[1] / "tools" / "recovery"
spec = importlib.util.spec_from_file_location("recovery_panel", RECOVERY / "panel.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


def snapshot(**changes):
    return {
        "version": 1,
        "operation": "install",
        "state": "running",
        "phase": "verify_partition",
        "partition": "data",
        "progress": {"completed": 2048, "total": 4096, "unit": "MiB"},
        "link": "connected",
        **changes,
    }


class RecoveryPanelTest(unittest.TestCase):
    def test_running_readback_shows_measured_bar(self):
        variables = panel.panel_variables(snapshot())
        self.assertEqual(variables["d9w_panel_phase"], "Verifying Data readback")
        self.assertEqual(variables["d9w_panel_counter"], "2,048 / 4,096 MiB")
        self.assertEqual(variables["d9w_panel_show_bar"], "1")
        self.assertEqual(variables["d9w_panel_percent"], "50")

    def test_unknown_total_shows_count_without_inventing_percentage(self):
        value = snapshot(progress={"completed": 8, "total": None, "unit": "items"},
                         phase="verify_source", partition=None)
        variables = panel.panel_variables(value)
        self.assertEqual(variables["d9w_panel_counter"], "8 items")
        self.assertEqual(variables["d9w_panel_show_bar"], "0")

    def test_verified_or_unknown_retains_history_without_an_active_bar(self):
        for state, title in (("verified", "Verified"), ("failed", "Failed"),
                             ("unknown", "Result unknown")):
            with self.subTest(state=state):
                variables = panel.panel_variables(snapshot(state=state, link="disconnected"))
                self.assertEqual(variables["d9w_panel_status"], title)
                self.assertEqual(variables["d9w_panel_link"], "Host disconnected")
                self.assertEqual(variables["d9w_panel_counter"], "Last reported 2,048 / 4,096 MiB")
                self.assertEqual(variables["d9w_panel_show_bar"], "0")

    def test_local_running_state_and_observer_link_are_independent(self):
        variables = panel.panel_variables(snapshot(link="disconnected"))
        self.assertEqual(variables["d9w_panel_status"], "In progress")
        self.assertEqual(variables["d9w_panel_link"], "Host disconnected")
        self.assertEqual(variables["d9w_panel_show_bar"], "1")

    def test_reboot_acknowledgement_does_not_claim_a_completed_boot(self):
        variables = panel.panel_variables(snapshot(operation="reboot", state="reboot_requested",
                                                   phase="reboot", partition=None, progress=None))
        self.assertEqual(variables["d9w_panel_status"], "Reboot requested")
        self.assertEqual(variables["d9w_panel_show_bar"], "0")
        self.assertEqual(variables["d9w_panel_counter"], "")

    def test_invalid_or_unbounded_input_is_rejected(self):
        for invalid in (snapshot(version=True), snapshot(state="raw user data"),
                        snapshot(phase=[], partition=None),
                        snapshot(progress={"completed": True, "total": 5, "unit": "items"}),
                        snapshot(progress={"completed": 5, "total": 4, "unit": "items"}),
                        snapshot(progress={"completed": 0, "total": 0, "unit": "items"})):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                panel.panel_variables(invalid)

    def test_template_binds_all_variables_without_any_input_action(self):
        path = RECOVERY / "twrp" / "d9w-operation-panel.xml"
        root = ET.parse(path).getroot()
        defaults = {entry.attrib["name"]: entry.attrib["value"]
                    for entry in root.findall("./variables/variable")}
        page = root.find("./pages/page[@name='d9w_operation_status']")
        self.assertEqual(root.tag, "recovery")
        self.assertIsNotNone(page)
        text_vars = set()
        for element in page.findall("./text/text"):
            variable = re.fullmatch(r"%(d9w_panel_[a-z_]+)%", element.text)
            self.assertIsNotNone(variable)
            text_vars.add(variable[1])
        bar = page.find("progressbar")
        bar_vars = {bar.find("condition").attrib["var1"], bar.find("data").attrib["name"]}
        self.assertEqual(set(defaults), text_vars | bar_vars)
        self.assertEqual(set(defaults), set(panel.panel_variables(snapshot())))
        self.assertEqual(defaults["d9w_panel_show_bar"], "0")
        self.assertEqual({node.tag for node in page},
                         {"background", "fill", "progressbar", "text"})
        for tag in ("action", "button", "slider", "touch"):
            self.assertIsNone(page.find(f".//{tag}"))

    def test_cli_renders_variable_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            path.write_text(json.dumps(snapshot()), encoding="utf-8")
            payload = subprocess.check_output([sys.executable, "-B", str(RECOVERY / "panel.py"), str(path)])
        self.assertEqual(json.loads(payload), panel.panel_variables(snapshot()))


if __name__ == "__main__":
    unittest.main()
