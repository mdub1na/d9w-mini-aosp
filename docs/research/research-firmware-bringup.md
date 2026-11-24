---
id: research-firmware-bringup
title: D9W Mini firmware bring-up evidence
type: research
status: active
---

# D9W Mini firmware bring-up evidence

The [firmware backlog](../../backlog.md) starts from a successful diagnostic boot on one D9W Mini. These observations describe that unit and image combination.

## Observed baseline

| Observation | Evidence and coverage |
| --- | --- |
| AOSP 12 Android UI became visible and airflow was observed. | Local R1 install receipt verified full System and Data readback. The Android log confirms `BOOT_COMPLETED` and the Cache record shows a single SystemServer start. The build used the pinned r34 inputs and the [boot-services preset](../../firmware/aosp12/bringup/boot-services.md). |
| Android blanked the display on idle timeout. | Logcat reports the display power transition and a caught Keyguard exception on sleep. Recovery retrieved the logs over UART. The captured evidence leaves full power-off and remote wake unconfirmed. |
| OEM telemetry was visible in the diagnostic boot. | A local guard sample reported the HAL ready and temperatures available at 105 seconds, with no fault at that sample. The trial was SELinux permissive. Thermal behavior, automatic protection and stability in enforcing mode remain open. |
| The framework lacked a valid WebView provider. | Logcat reports both a missing valid provider and a missing `libwebviewchromium_loader.so`. |
| Stock rollback and UART access are available. | The paired stock System/Data restore and return to Android were observed in the [recovery record](../recovery-status.md). The R1 host has since retrieved first-boot records and Android logs. The R2 image and panel compile passed offline. Hardware validation is [B-01](../backlog/B-01-recovery-r2.md). |
| The selected TV APKs passed integrity checks on the host. | The locally retained packages match the chosen app set. The stock trials used working Android app data. First launch and package defaults from clean AOSP Data require separate validation. |

## Decisions and open questions

- Use r34 with the stock kernel and Vendor for the first usable profile. The existing public configuration remains the baseline for validating ABI and storage geometry.
- Preserve the distinction between a boot event, a responsive remote-controlled interface and an end-to-end firmware pass. A joined run is useful after each subsystem has at least one independently attributable result.
- Keep the experimental guard during short development runs. Establish shutdown and cooling behavior and investigate the unresolved kernel/vendor compatibility check before treating the image as suitable for daily use.
- Treat the optical controls as an OEM integration. The settings shortcut can only open the OEM UI once its target activity, native services and permissions are working.

## Code anchors

| Area | Code |
| --- | --- |
| Pinned platform inputs | `firmware/aosp12/source-baseline.json` |
| Public product profile | `firmware/aosp12/device/aosp_d9wmini.mk` |
| TV SystemUI change | `firmware/aosp12/bringup/systemui-lockscreen-lifecycle.patch` |
| Host configuration checks | `tests/test_aosp12_config.py` |
| Recovery status source | `tools/recovery/progress.py` |
