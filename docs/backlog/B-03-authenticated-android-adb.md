---
id: B-03
title: "Verify Wi-Fi, Ethernet and authenticated Android ADB"
status: open
priority: P0
size: M
stage: daily-base
blocked_by: []
---

# B-03 — Verify Wi-Fi, Ethernet and authenticated Android ADB

First-boot evidence shows Android started its diagnostic ADB service and
detected the Ethernet interface. An authenticated connection from the host and
on-device Wi-Fi operation still need a device check.

Verify the network path from Android so debug access remains available when
testing a separate recovery image. Keep host keys and addresses in local
configuration.

## Acceptance

- Wi-Fi and Ethernet each obtain an address and pass a connectivity check.
  Reconnect after one sleep and wake cycle and record the result for each path.
- The authorized host opens an ADB shell after a normal Android boot and
  verifies boot completion and the expected device and recovery partition
  with read-only commands.
- The diagnostic build rejects an unapproved ADB key. The release profile
  starts with remote debugging disabled.

| Code anchor | Purpose |
| --- | --- |
| `firmware/aosp12/device/aosp_d9wmini.mk` | Android TV product baseline. |
| `firmware/aosp12/device/device.mk` | Device-level configuration entry point. |
