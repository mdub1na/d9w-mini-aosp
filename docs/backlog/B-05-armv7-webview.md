---
id: B-05
title: "Restore a working ARMv7 WebView"
status: open
priority: P1
size: M
stage: core-apps
blocked_by: [B-04]
---

# B-05 — Restore a working ARMv7 WebView

During the first boot, WebViewUpdateService reported that it had no loadable
provider. The framework also reported that it could not load
`libwebviewchromium_loader.so`. User apps may need WebView for sign-in and
embedded pages.

Choose an Android 12 provider with ARMv7 native libraries and a documented
update path. Integrate its loader and framework configuration in the local
profile from [B-04](B-04-reproducible-system-trial.md).

## Acceptance

- The image contains the approved signed provider and its required ARM32
  native dependencies.
- After a clean boot, Android selects that provider and an ordinary test app
  renders a local page in WebView without loader or provider errors.
- On a connected test device, WebView loads an HTTPS page and follows a
  test redirect without relying on Google services.

| Code anchor | Purpose |
| --- | --- |
| `firmware/aosp12/bringup/boot-services.mk` | Current optional System-side package preset. |
| `firmware/aosp12/device/BoardConfig.mk` | ARM32 architecture and partition constraints. |
