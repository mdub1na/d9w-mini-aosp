---
id: B-08
title: "Restore focus, geometry and the projector settings entry point"
status: open
priority: P1
size: L
stage: hardware
blocked_by: [B-04]
---

# B-08 — Restore focus, geometry and the projector settings entry point

The stock settings UI calls projector-specific components for focus and geometry. Identify the matching services, native libraries, permissions and configuration from the local stock reference. Add the minimum System-side dependencies to the [private profile](B-04-reproducible-system-trial.md), then bind the shortcut to the working settings entry point. Use short device sessions until [projector safety](B-07-qualify-projection-safety.md) is qualified.

- The shortcut opens the projector settings from the TV home screen. The remote can select a setting and return to Home.
- Manual focus moves in both directions, and autofocus, if part of the stock configuration, completes once on request. Geometry adjustment visibly changes the projected image and saves the selected configuration across a reboot.
- Record the service and permission paths needed on the enforcing candidate. Restore the prior user-visible focus and geometry settings after the test.

## Code anchors

| Area | Code |
| --- | --- |
| System-side device properties | `firmware/aosp12/device/device.mk` |
| Hardware ABI and Vendor interface | `firmware/aosp12/device/BoardConfig.mk` |
