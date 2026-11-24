---
id: B-04
title: "Reproduce the local System trial from pinned inputs"
status: open
priority: P0
size: L
stage: core-apps
blocked_by: [B-02]
---

# B-04 — Reproduce the local System trial from pinned inputs

The current public product checks the build configuration with image producers
disabled. A separate local System image based on Android 12 r34 reached the
interface with the stock kernel and Vendor. Put the working recipe behind an
explicit trial product so additional apps can share the same baseline.

Start host builds while [B-02](B-02-remote-sleep-wake.md) is open. Use the
sleep/wake result before the first flash of this profile. The recipe should
resolve owner-supplied inputs locally and produce a System artifact and an input
manifest.

## Acceptance

- The documented Linux build from pinned inputs produces a System image that
  fits the stock partition and passes offline filesystem and contents checks.
- The trial records source revisions, image hash, build flags and its exact
  required stock inputs. Only the explicit trial product enables System image
  production.
- Recovery verifies the input and the full write, then the profile completes a
  cold boot on clean Data. A known-good System/Data pair remains available
  for rollback.

| Code anchor | Purpose |
| --- | --- |
| `firmware/aosp12/source-baseline.json` | Pinned AOSP release and source manifest. |
| `firmware/aosp12/device/aosp_d9wmini.mk` | Configuration-only product and image gates. |
| `firmware/aosp12/check_config.py` | Resolved configuration checks. |
