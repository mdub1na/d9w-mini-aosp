import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
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

    def test_hdpi_template_can_only_navigate_back_to_existing_menus(self):
        path = RECOVERY / "twrp" / "d9w-operation-panel-hdpi.xml"
        root = ET.parse(path).getroot()
        defaults = {entry.attrib["name"] for entry in root.findall("./variables/variable")}
        self.assertEqual(defaults, {*panel.panel_variables(snapshot()), "d9w_panel_hdpi_available"})
        page = root.find("./pages/page[@name='d9w_operation_status']")
        self.assertIsNotNone(page)
        actions = page.findall(".//action[@function]")
        self.assertEqual([(entry.attrib["function"], entry.text) for entry in actions],
                         [("page", "advanced"), ("page", "advanced"), ("page", "main")])
        for navigation in (*page.findall("button"), *page.findall("action")):
            self.assertEqual(navigation.find("condition").attrib, {"var1": "tw_busy", "var2": "0"})
        bar = page.find("progressbar")
        self.assertEqual(bar.find("resource").attrib, {"empty": "progress_empty", "full": "progress_full"})
        self.assertEqual(bar.find("placement").get("x"), str((1920 - 816) // 2))
        for position in page.findall(".//placement"):
            self.assertLessEqual(int(position.get("x")) + int(position.get("w", "0")), 1920)
            self.assertLessEqual(int(position.get("y")) + int(position.get("h", "0")), 1200)

    @unittest.skipUnless(os.environ.get("D9W_TWRP_SOURCE"), "R1 TeamWin source is unavailable")
    def test_hdpi_theme_and_navigation_with_r1_source(self):
        source = Path(os.environ["D9W_TWRP_SOURCE"]).resolve()
        twrp = RECOVERY / "twrp"
        files = ("gui/Android.bp", "gui/gui.cpp", "gui/theme/common/landscape.xml",
                 "gui/theme/landscape_hdpi/ui.xml")
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for filename in files:
                target = work / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / filename, target)
            patch = str(twrp / "twrp-operation-panel.patch")
            subprocess.run(["git", "apply", "--check", patch], cwd=work, check=True)
            subprocess.run(["git", "apply", patch], cwd=work, check=True)
            hdpi = work / "gui/theme/landscape_hdpi"
            page = hdpi / "d9w-operation-panel-hdpi.xml"
            shutil.copyfile(twrp / page.name, page)
            theme = ET.parse(hdpi / "ui.xml").getroot()
            self.assertEqual(theme.find("./details/resolution").attrib, {"width": "1920", "height": "1200"})
            self.assertIn(page.name, {item.get("name") for item in theme.findall("./include/xmlfile")})
            menus_path = work / "gui/theme/common/landscape.xml"
            menus = ET.parse(menus_path).getroot()
            entry = menus.find("./pages/page[@name='advanced']/button/action[.='d9w_operation_status']")
            self.assertIsNotNone(entry)
            self.assertEqual(entry.get("function"), "page")
            self.assertIsNotNone(menus.find("./pages/page[@name='main']"))
            for bar in ("progress_empty", "progress_full"):
                image = theme.find(f"./resources/image[@name='{bar}']")
                path = source / "gui/theme/landscape_hdpi/images" / (image.get("filename") + ".png")
                with path.open("rb") as stream:
                    header = stream.read(24)
                self.assertEqual(struct.unpack(">II", header[16:24]), (816, 72))
            for font in ET.parse(page).findall("./resources/font"):
                self.assertTrue((source / "gui/theme/common/fonts" / font.get("filename")).is_file())
            fixture = work / "recovery_panel_theme"
            subprocess.run([os.environ.get("CXX", "c++"), "-std=c++11", "-I", str(source / "gui"),
                            str(Path(__file__).with_name("recovery_panel_theme.cpp")),
                            "-o", str(fixture)], check=True)
            subprocess.run([str(fixture), str(hdpi / "ui.xml"), str(menus_path), str(page)], check=True)

    def test_native_panel_reads_local_snapshot_with_a_disconnected_host(self):
        native = RECOVERY / "native"
        twrp = RECOVERY / "twrp"
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            core = work / "operation_status.o"
            fixture = work / "recovery_panel_native"
            subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-c", str(native / "operation_status.c"), "-o", str(core)], check=True)
            subprocess.run([os.environ.get("CXX", "c++"), "-std=c++11", "-Wall", "-Wextra", "-Werror",
                            "-I", str(native), "-I", str(twrp),
                            str(Path(__file__).with_name("recovery_panel_native.cpp")),
                            str(twrp / "d9w_operation_panel.cpp"), str(core), "-o", str(fixture)], check=True)
            subprocess.run([str(fixture), directory], check=True)

    def test_cli_renders_variable_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            path.write_text(json.dumps(snapshot()), encoding="utf-8")
            payload = subprocess.check_output([sys.executable, "-B", str(RECOVERY / "panel.py"), str(path)])
        self.assertEqual(json.loads(payload), panel.panel_variables(snapshot()))


if __name__ == "__main__":
    unittest.main()
