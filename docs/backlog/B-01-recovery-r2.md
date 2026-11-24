---
id: B-01
title: Verify the Recovery R2 operation screen
status: wip
priority: P0
size: S
stage: recovery
blocked_by: []
---

# B-01 — Verify the Recovery R2 operation screen

R1 can run a signed command from Mac over UART and report its result. R2 adds an HDPI operation screen. The offline image build and fixed-window checks passed. The remaining proof is on the projector.

## Acceptance

- Establish an independent path to restore the retained R1 image and confirm the current Recovery identity. Write and fully read back only the Recovery partition.
- Open **Advanced → Operation status** with the remote. Send a read-only UART preflight and observe its actual result on screen. Exercise Back and return to Android.
- During the next separately authorized operation with measured progress, compare the on-screen phase and count with the local writer output. Record the result and the rollback path in the device evidence.

## Code anchors

| Area | Code |
| --- | --- |
| Status and result model | `tools/recovery/progress.py` |
| UI projection | `tools/recovery/panel.py` |
| Host UI tests | `tests/test_recovery_panel.py` |
