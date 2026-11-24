---
id: B-06
title: "Integrate Plume, Ultimate File Manager and VLC"
status: open
priority: P1
size: M
stage: core-apps
blocked_by: [B-04]
---

# B-06 — Integrate Plume, Ultimate File Manager and VLC

Plume, Ultimate File Manager FOSS TV and VLC are the first agreed app group.
Their signed APKs have been staged locally and used on stock. The clean AOSP
trial still needs to validate its preinstalls and default handlers.

Add an optional app profile to the [local System trial](B-04-reproducible-system-trial.md).
Pin APK versions and digests, preserve their signatures and install them with
ordinary app permissions. Resolve redistribution rights before shipping a
bundle that contains third-party APKs.

## Acceptance

- On clean Data, Android locates all three apps in System and selects Plume
  as Home after reboot. D-pad navigation and Home work with the physical
  remote.
- Ultimate File Manager opens a test file on CODEX through Android's storage
  permission flow.
- VLC opens a local test clip with picture and sound through the selected
  video handler. Back returns to the file manager.
- The artifact report identifies the preinstall profile and shows it fits in
  the existing System partition.

| Code anchor | Purpose |
| --- | --- |
| `firmware/aosp12/bringup/boot-services.mk` | Example of an opt-in System preset. |
| `firmware/aosp12/device/aosp_d9wmini.mk` | TV product configuration inherited by the trial. |
