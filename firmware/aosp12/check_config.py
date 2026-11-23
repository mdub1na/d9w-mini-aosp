#!/usr/bin/env python3
"""Run configuration-only dumpvars in a disposable view of a retained Linux tree."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

IMAGE_PARTS = ('SYSTEM', 'SYSTEM_OTHER', 'SYSTEM_EXT', 'PRODUCT', 'VENDOR', 'ODM',
               'VENDOR_DLKM', 'ODM_DLKM', 'BOOT', 'VENDOR_BOOT', 'RECOVERY',
               'RAMDISK', 'USERDATA', 'CACHE', 'VBMETA', 'SUPER_EMPTY')
EXPECTED = {'TARGET_ARCH':'arm', 'TARGET_ARCH_VARIANT':'armv7-a-neon',
            'TARGET_CPU_ABI':'armeabi-v7a', 'TARGET_CPU_ABI2':'armeabi',
            'TARGET_2ND_ARCH':'',
            'TARGET_USES_64_BIT_BINDER':'true', 'TARGET_NO_KERNEL':'true',
            'TARGET_NO_RECOVERY':'true', 'BOARD_BUILD_SYSTEM_ROOT_IMAGE':'true',
            'BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE':'ext4',
            'BOARD_SYSTEMIMAGE_PARTITION_SIZE':'1862270976',
            'TARGET_COPY_OUT_VENDOR':'vendor', 'TARGET_COPY_OUT_SYSTEM_EXT':'system/system_ext',
            'TARGET_COPY_OUT_PRODUCT':'system/product',
            'PRODUCT_USE_DYNAMIC_PARTITIONS':'false', 'PRODUCT_BUILD_SUPER_PARTITION':'false',
            'PRODUCT_ENFORCE_VINTF_MANIFEST':'true', 'PRODUCT_FULL_TREBLE':'true',
            'PRODUCT_FULL_TREBLE_OVERRIDE':'true'}
VARS = (list(EXPECTED) + ['PLATFORM_SDK_VERSION', 'PLATFORM_VERSION', 'PLATFORM_VNDK_VERSION',
        'BOARD_VNDK_VERSION', 'PRODUCT_SHIPPING_API_LEVEL',
        'ALLOW_MISSING_DEPENDENCIES'] +
        ['PRODUCT_BUILD_' + part + '_IMAGE' for part in IMAGE_PARTS] +
        ['BUILDING_' + part + '_IMAGE' for part in IMAGE_PARTS])


def parse_dump(text):
    result = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = shlex.split(line, posix=True)
        if len(fields) != 1 or '=' not in fields[0]:
            raise ValueError('Malformed configuration dump')
        key, value = fields[0].split('=', 1)
        if key not in VARS or key in result:
            raise ValueError('Unknown or duplicate configuration variable')
        result[key] = value
    if set(result) != set(VARS):
        raise ValueError('Incomplete configuration dump')
    return result


def validate(values):
    for key, value in EXPECTED.items():
        if values.get(key) != value:
            raise ValueError('Wrong preparation value: ' + key)
    sdk = values.get('PLATFORM_SDK_VERSION')
    platform_vndk = values.get('PLATFORM_VNDK_VERSION')
    board_vndk = values.get('BOARD_VNDK_VERSION')
    if (sdk, platform_vndk, board_vndk) not in (('31', '31', 'current'), ('32', '32', '31')):
        raise ValueError('Expected API 31 with current VNDK or API 32 reference with VNDK 31')
    effective_vndk = platform_vndk if board_vndk == 'current' else board_vndk
    for part in IMAGE_PARTS:
        if values.get('PRODUCT_BUILD_' + part + '_IMAGE') != 'false':
            raise ValueError('Image generation must remain disabled: ' + part)
        if values.get('BUILDING_' + part + '_IMAGE') != '':
            raise ValueError('Android enabled an image producer: ' + part)
    if values.get('PRODUCT_SHIPPING_API_LEVEL'):
        raise ValueError('Shipping API remains unresolved')
    if values.get('ALLOW_MISSING_DEPENDENCIES'):
        raise ValueError('Missing dependency waivers must not be enabled')
    return {'schema_version':1, 'status':'NOT_FLASHABLE', 'configuration_checks_passed':True,
            'observed_source_api':sdk, 'baseline_api31_observed':sdk == '31',
            'effective_vendor_vndk_version':effective_vndk,
            'full_source_manifest_pinned':False, 'system_build_tested':False,
            'oem_compatibility_verified':False, 'device_trial_ready':False,
            'values':values}


def run(source, tree):
    source, tree = source.resolve(), tree.resolve()
    ui = source / 'out/soong_ui'
    if not ui.is_file() or not (source / 'build/make/core/main.mk').is_file():
        raise ValueError('A retained Linux checkout and existing host soong_ui are required')
    with tempfile.TemporaryDirectory(prefix='d9w-aosp-config-') as directory:
        scratch = Path(directory)
        view = scratch / 'source'
        view.mkdir()
        for path in source.iterdir():
            if path.name not in ('device', 'out'):
                (view / path.name).symlink_to(path, target_is_directory=path.is_dir())
        target = view / 'device/flixtone/d9wmini_aosp'
        target.parent.mkdir(parents=True)
        # Copy only the small candidate, never alter the retained source checkout.
        import shutil
        shutil.copytree(tree, target)
        env = dict(os.environ)
        for name in ('ALLOW_MISSING_DEPENDENCIES', 'TARGET_BUILD_APPS', 'TARGET_BUILD_UNBUNDLED',
                     'OUT_DIR_COMMON_BASE', 'DIST_DIR', 'SOONG_OUT_DIR', 'SOONG_UI_LOGDIR'):
            env.pop(name, None)
        env.update(OUT_DIR=str(scratch/'out'), ANDROID_BUILD_TOP=str(view),
                   TARGET_PRODUCT='aosp_d9wmini', TARGET_BUILD_VARIANT='userdebug',
                   TARGET_BUILD_TYPE='release', TMPDIR=str(scratch))
        result = subprocess.run([str(ui), '--dumpvars-mode', '--vars=' + ' '.join(VARS)],
                                cwd=view, env=env, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise ValueError('Android configuration failed:\n' + result.stdout + result.stderr)
        return validate(parse_dump(result.stdout))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--device-tree', type=Path, default=Path(__file__).resolve().parent/'device')
    args = parser.parse_args()
    try:
        report = run(args.source, args.device_tree)
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, str(error)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
