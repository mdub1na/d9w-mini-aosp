# D9W Mini AOSP 12 configuration

## Contents

- [Destiny](#destiny)
- [Project structure](#project-structure)
- [Stack and tools](#stack-and-tools)
- [Run the host tests](#run-the-host-tests)
- [Check resolved Android configuration](#check-resolved-android-configuration)
- [Source baseline and target](#source-baseline-and-target)

## Destiny

This directory defines a configuration-only Android 12 target for developers working on the Flixtone D9W Mini. It specifies an ARM32 System for use with the existing kernel and Vendor partition. Start with the host tests to check the configuration contracts. All image producers are disabled in this snapshot.

## Project structure

```text
├── check_config.py        # Runs and validates Android dumpvars in a temporary source view
├── device/                # Device makefiles for aosp_d9wmini-userdebug
│   ├── AndroidProducts.mk # Registers the product and build variant
│   ├── BoardConfig.mk     # Selects the ABI, filesystem, partition size and VNDK
│   ├── aosp_d9wmini.mk    # Sets the product configuration and disables image generation
│   └── device.mk          # Marks the product as configuration-only
└── source-baseline.json   # Records the verified Android 12 revisions and digests
```

## Stack and tools

| Tool or platform | Purpose |
| --- | --- |
| Android 12 AOSP, API 31 | Platform baseline for the System target |
| Android build Makefiles | Define the product, ABI and stock partition layout |
| Soong UI | Resolves Android build variables in an existing Linux checkout |
| Python 3 and unittest | Validate the resolved variables and run synthetic host tests |

## Run the host tests

From the repository root, run the six tests with Python 3.

```sh
python3 -E -B -m unittest discover -s tests -p 'test_aosp12_config.py' -v
```

The tests use synthetic variable dumps and exercise the ABI, filesystem layout, VNDK selection and disabled image producers.

## Check resolved Android configuration

Use a Linux AOSP checkout with an existing executable `out/soong_ui` and the Android build dependencies available. Set `AOSP_SOURCE` to the checkout path, then run from the repository root.

```sh
python3 -E -B firmware/aosp12/check_config.py --source "$AOSP_SOURCE"
```

The validator runs `soong_ui --dumpvars-mode` in a temporary source view and writes a JSON report to standard output. A successful check reports `configuration_checks_passed: true` and `status: NOT_FLASHABLE`. Source revision verification is a separate step.

## Source baseline and target

[The source record](source-baseline.json) pins the official `android-12.0.0_r34` manifest, superproject and build/make revisions. It preserves the digest of the revision table that matches all 1,048 manifest projects. The `source_sync_performed` field applies to that revision audit.

The target uses ARMv7 with NEON and 64-bit Binder transactions. It retains the stock ext4 System-as-root layout and a System partition size of 1,862,270,976 bytes. On API 31, `BOARD_VNDK_VERSION=current` resolves to VNDK 31 for the stock Vendor partition. The validator also accepts an API 32 reference with the VNDK 31 snapshot for configuration checks. Shipping API history and OEM compatibility remain open. VINTF enforcement remains enabled.
