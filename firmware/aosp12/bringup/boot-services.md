# AOSP 12 boot services

The optional preset supplies the metadata package requested by the framework
and keeps FusedLocation in the System trial. The TV SystemUI already selects
`TvSystemUIFactory` and `TvStatusBar`. Its wake callback still reached the
phone keyguard view manager before any phone status bar was registered.
The patch guards the shade animation callbacks and the sleep-completion
bouncer callback when their phone UI objects are unavailable.

## Apply to a System trial

Use the pinned Android 12 r34 sources and an isolated trial checkout. Set
`AOSP_SRC` to its root and `PRESET_DIR` to this directory's absolute path.
From the Linux build environment, check the source pins and apply the patch.

```sh
(
    set -eu
    frameworks_base="$AOSP_SRC/frameworks/base"
    module_metadata="$AOSP_SRC/packages/modules/ModuleMetadata"
    lifecycle=packages/SystemUI/src/com/android/systemui/statusbar/phone/StatusBarKeyguardViewManager.java
    test "$(git -C "$frameworks_base" rev-parse HEAD)" = 9ea17a554d1cb8c895ac0fa3c1b3513309817d69
    test "$(git -C "$module_metadata" rev-parse HEAD)" = 0e411d5f1f227d8baf4059ef1e9e4fe1ad1e20c5
    printf '%s  %s\n' \
        35f68e33741a33f7ad59cee9b47995f03423ad43aca47287b2dca2b376e85fc4 \
        "$frameworks_base/$lifecycle" | sha256sum -c -
    git -C "$frameworks_base" apply --check "$PRESET_DIR/systemui-lockscreen-lifecycle.patch"
    git -C "$frameworks_base" apply "$PRESET_DIR/systemui-lockscreen-lifecycle.patch"
)
```

Use `inherit-product` to include `boot-services.mk` in the reviewed System
trial product. The public configuration-only product keeps all image producers
disabled. ModuleMetadata is an upstream product-specific APK. In a System
trial that folds Product into System, validate the APK within that Product
subtree. Confirm its manifest identifies `com.android.modulemetadata` and that
the framework selects the same provider.

## Verify the result

The host tests compile the patched lifecycle callbacks against small Java
stubs. They cover missing TV UI objects, an unattached notification shade
and the unchanged animation and bouncer calls when the phone UI is present.
Run them from the repository root with Python, Git and a JDK:

```sh
python3 -B -m unittest discover -s tests -p test_aosp12_config.py
```

To exercise the patch against the complete pinned Java source in that test,
set `D9W_AOSP12_STATUSBAR_SOURCE` to the absolute path of the original Java
file. The test checks its digest and applies the patch to a temporary copy.

A separate image check must verify the metadata APK and the patched SystemUI
APK together. The runtime acceptance check is a cold boot to a responsive
interface followed by one sleep and wake cycle. Check that the TV status bar
starts and that the captured log is free of the missing-metadata and
phone-shade exceptions. The test results here cover the source preset.
A candidate image and runtime compatibility require those separate checks.
