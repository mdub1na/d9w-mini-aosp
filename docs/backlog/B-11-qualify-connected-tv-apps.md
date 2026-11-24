---
id: B-11
title: "Qualify Kinopoisk TV and Rutube TV without Google services"
status: open
priority: P1
size: M
stage: connected
blocked_by: [B-03, B-05]
---

# B-11 — Qualify Kinopoisk TV and Rutube TV without Google services

Kinopoisk TV and Rutube TV belong to the selected connected-app profile. The previous stock tests establish their behavior on that system. A clean AOSP build needs its own comparison with the app versions, input paths and account requirements recorded. Reuse the [network](B-03-authenticated-android-adb.md), [WebView](B-05-armv7-webview.md) and [media](B-09-qualify-av-paths.md) evidence.

- With the remote, open each app, reach the catalog and exercise the supported sign-in flow with an authorized test account when required. Record the point of failure if an app requires an unavailable service.
- For at least one accessible title per app, test playback, sound, pause and seek where supported. Record codec, DRM or network errors separately from sign-in errors. Run with Google Play services and Play Store absent.

## Code anchors

| Area | Code |
| --- | --- |
| TV profile and app integration | `firmware/aosp12/device/aosp_d9wmini.mk` |
| Android API and ABI baseline | `firmware/aosp12/device/BoardConfig.mk` |
