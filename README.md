# D9W Mini AOSP 12

## Contents

- [Destiny](#destiny)
- [Project structure](#project-structure)
- [Stack and tools](#stack-and-tools)
- [Run the configuration checks](#run-the-configuration-checks)
- [Device status](#device-status)
- [License](#license)

## Destiny

This repository provides an Android 12 AOSP device and product configuration for the Flixtone D9W Mini projector. It gives developers a starting point for validating a System target that retains the stock kernel, Vendor partition, and storage layout. The published target has all image producers disabled.

## Project structure

```text
.
├── .github/workflows/checks.yml # Host validation on GitHub Actions
├── docs/recovery-status.md      # Observed boot, UART recovery, and stock return
├── firmware/aosp12/
│   ├── device/                 # Board and product Make configuration
│   ├── check_config.py         # Validator for resolved Android build variables
│   ├── source-baseline.json    # Pinned official Android 12 revisions
│   └── README.md               # Configuration scope and validator usage
├── tests/test_aosp12_config.py  # Offline cases for the configuration contract
└── LICENSE                     # Apache License 2.0 for project sources and docs
```

## Stack and tools

| Tool | Purpose in this project |
| --- | --- |
| AOSP `android-12.0.0_r34` | Android 12 source baseline for the API 31 configuration |
| Android product and board Make files | ARM32 userspace with the Binder64 transaction layout and the stock System partition geometry |
| Python 3 and `unittest` | Check resolved build variables and test the validator with synthetic input |
| GitHub Actions | Run the host test suite on changes |

## Run the configuration checks

Run the tests with Python 3 from the repository root.

```sh
python3 -E -B -m unittest discover -s tests -p test_aosp12_config.py -v
```

The tests cover the target ABI, the Android version and Vendor interface selection, partition geometry, and the disabled image producers. See the [configuration guide](firmware/aosp12/README.md) for checking resolved build variables from an AOSP source tree.

## Device status

A separate AOSP experiment reached the Android boot animation and an interactive UART shell. The projector powered off before its graphical interface loaded. UART subsequently opened the installed TWRP, and restoring the paired stock System and Data brought back Android. See the [recovery status](docs/recovery-status.md) for the observations and conditions.

## License

Copyright 2026 mdub1na. The project source and documentation are licensed under [Apache-2.0](LICENSE). Upstream Android components referenced by the configuration retain their own licenses.
