---
id: B-12
title: "Qualify the integrated release candidate and rehearse rollback"
status: open
priority: P1
size: L
stage: release
blocked_by: [B-01, B-06, B-07, B-08, B-09, B-10, B-11]
---

# B-12 — Qualify the integrated release candidate and rehearse rollback

The separate device checks qualify individual paths. Run them together on a single versioned candidate from clean Data. Keep a record of source revisions, input digests, enabled profiles, system package versions and the recovery version. Use the earlier [paired-restore evidence](../recovery-status.md) to plan a fresh rehearsal for this candidate.

- Check cold boot, Home, sleep and wake, projection and thermal behavior, optical controls, HDMI, sound and local playback, connectivity, installation and updates, and connected-app playback. Record passes, failures and skipped cases against the same candidate and hardware.
- Keep Boot, Vendor and partition geometry bound to the agreed baseline. Protect the owner's current data before testing restore. Rehearse the paired stock return and confirm readback plus an observed Android boot. Record which recovery and ADB routes were exercised.
- Publish build instructions, the test matrix and the rollback procedure with the supported scope. Keep private bindings, credentials, raw device data and restricted binaries out of the public release.

## Code anchors

| Area | Code |
| --- | --- |
| AOSP revision and geometry pins | `firmware/aosp12/source-baseline.json`, `firmware/aosp12/device/BoardConfig.mk` |
| Resolved configuration validation | `firmware/aosp12/check_config.py` |
| Recovery operation result checks | `tools/recovery/progress.py`, `tests/test_recovery_progress.py` |
