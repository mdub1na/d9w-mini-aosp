---
id: B-10
title: "Qualify RuStore TV installs and updates"
status: open
priority: P1
size: M
stage: connected
blocked_by: [B-03, B-04]
---

# B-10 — Qualify RuStore TV installs and updates

RuStore TV is the selected store for the AOSP profile. Validate its publisher-signed APK and the Android installer path on clean Data. Use the documented [connectivity check](B-03-authenticated-android-adb.md) and include the [WebView result](B-05-armv7-webview.md) if RuStore invokes embedded sign-in.

- The remote opens the store, navigates to a designated test app and completes installation through Android's consent UI. The new app appears on Home and launches.
- An update from the same signer succeeds and preserves app data. An incompatible signer is rejected by the package installer. Record the store and test-app versions and the installer decisions.
- Keep the app's original signature and use ordinary package permissions. Check the selected store on a clean profile without Play Store or Google Play services.

## Code anchors

| Area | Code |
| --- | --- |
| TV product and place to bind the private app profile | `firmware/aosp12/device/aosp_d9wmini.mk` |
| Product configuration validation | `firmware/aosp12/check_config.py` |
