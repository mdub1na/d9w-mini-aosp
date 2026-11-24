"""Host-only gates for the AOSP configuration preparation; no Docker or device."""
import importlib.util
from pathlib import Path
import unittest

from aosp12_boot_services import verify_lifecycle

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('aosp12_config', ROOT/'firmware/aosp12/check_config.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def fixture():
    values = {key:'' for key in C.VARS}
    values.update(C.EXPECTED)
    values.update({'PRODUCT_BUILD_'+part+'_IMAGE':'false' for part in C.IMAGE_PARTS})
    values.update(PLATFORM_SDK_VERSION='32', PLATFORM_VERSION='12',
                  PLATFORM_VNDK_VERSION='32', BOARD_VNDK_VERSION='31')
    return values


class Aosp12Configuration(unittest.TestCase):
    def test_boot_services_preset_is_separate_from_the_default_product(self):
        device = ROOT / "firmware/aosp12/device"
        for path in device.glob("*.mk"):
            self.assertNotIn("boot-services.mk", path.read_text(encoding="utf-8"))
        preset = ROOT / "firmware/aosp12/bringup/boot-services.mk"
        body = " ".join(
            line.strip().removesuffix("\\").strip()
            for line in preset.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        self.assertEqual(body, "PRODUCT_PACKAGES += FusedLocation ModuleMetadata")

    def test_systemui_sleep_wake_with_and_without_phone_shade(self):
        verify_lifecycle(ROOT / "firmware/aosp12/bringup/systemui-lockscreen-lifecycle.patch")

    def test_reference_configuration_does_not_claim_api31_or_flashability(self):
        result = C.validate(fixture())
        self.assertTrue(result['configuration_checks_passed'])
        self.assertFalse(result['baseline_api31_observed'])
        self.assertEqual(result['effective_vendor_vndk_version'], '31')
        self.assertEqual(result['status'], 'NOT_FLASHABLE')
        for field in ('full_source_manifest_pinned', 'system_build_tested',
                      'oem_compatibility_verified', 'device_trial_ready'):
            self.assertFalse(result[field])

    def test_api31_uses_current_vndk_and_rejects_other_source_pairs(self):
        baseline = fixture()
        baseline.update(PLATFORM_SDK_VERSION='31', PLATFORM_VNDK_VERSION='31',
                        BOARD_VNDK_VERSION='current')
        result = C.validate(baseline)
        self.assertTrue(result['baseline_api31_observed'])
        self.assertEqual(result['effective_vendor_vndk_version'], '31')
        for sdk, platform, board in [('31', '31', '31'), ('32', '32', 'current'),
                                     ('31', '32', '31'), ('32', '31', 'current'),
                                     ('33', '33', '31'), ('31', '', 'current')]:
            values = dict(baseline, PLATFORM_SDK_VERSION=sdk, PLATFORM_VNDK_VERSION=platform,
                          BOARD_VNDK_VERSION=board)
            with self.subTest(sdk=sdk, platform=platform, board=board), self.assertRaises(ValueError):
                C.validate(values)

    def test_each_image_producer_is_disabled_at_product_and_resolved_level(self):
        for part in C.IMAGE_PARTS:
            for prefix, value in [('PRODUCT_BUILD_', 'true'), ('BUILDING_', 'true'),
                                  ('BUILDING_', 'false'), ('BUILDING_', '1')]:
                values = fixture(); values[prefix+part+'_IMAGE'] = value
                with self.subTest(part=part, prefix=prefix), self.assertRaises(ValueError):
                    C.validate(values)

    def test_wrong_abi_geometry_or_sar_is_rejected(self):
        for key, value in [('TARGET_ARCH','arm64'), ('TARGET_CPU_ABI','arm64-v8a'),
                           ('TARGET_2ND_ARCH','arm64'), ('TARGET_USES_64_BIT_BINDER','false'),
                           ('BOARD_SYSTEMIMAGE_PARTITION_SIZE','1862270975'),
                           ('BOARD_BUILD_SYSTEM_ROOT_IMAGE','false'),
                           ('PRODUCT_USE_DYNAMIC_PARTITIONS','true'), ('TARGET_COPY_OUT_VENDOR','system/vendor')]:
            values = fixture(); values[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): C.validate(values)

    def test_launch_or_compatibility_waivers_do_not_make_the_check_green(self):
        for key, value in [('PRODUCT_SHIPPING_API_LEVEL','31'),
                           ('PRODUCT_ENFORCE_VINTF_MANIFEST','false'),
                           ('PRODUCT_FULL_TREBLE','false'),
                           ('PRODUCT_FULL_TREBLE_OVERRIDE','false'),
                           ('ALLOW_MISSING_DEPENDENCIES','true')]:
            values = fixture(); values[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): C.validate(values)

    def test_dump_parser_is_data_only_and_requires_every_unique_key(self):
        good = '\n'.join(key+'='+repr(value) for key,value in fixture().items())
        self.assertEqual(C.parse_dump(good), fixture())
        for bad in (good+'\nUNKNOWN=x', good+'\nTARGET_ARCH=arm',
                    '\n'.join(good.splitlines()[1:]), good+'\n$(touch /tmp/aosp-config-test)'):
            with self.subTest(value=bad[-60:]), self.assertRaises(ValueError): C.parse_dump(bad)


if __name__ == '__main__':
    unittest.main()
