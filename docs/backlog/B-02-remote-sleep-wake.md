---
id: B-02
title: "Make remote navigation and sleep/wake repeatable"
status: open
priority: P0
size: M
stage: daily-base
blocked_by: []
---

# B-02 — Make remote navigation and sleep/wake repeatable

The first System trial reached `BOOT_COMPLETED` and displayed the Android
interface. After the idle timeout, Android requested display sleep. SystemUI
then logged a caught null AlarmManager exception in
`KeyguardViewMediator.doKeyguardLaterLocked()`. The cause of the final loss of
projection remains open.

Reproduce the idle and remote Power paths separately. Trace Keyguard
initialization and the vendor display and power transitions. Keep the
diagnostic cutoff active during the comparison.

## Acceptance

- From a cold boot, D-pad, OK, Back and Home work on the launcher and in
  Settings.
- The projector sleeps and wakes on the same boot session for both paths.
  Logs identify the transition and show no recurrence of the observed
  Keyguard exception or SystemUI restart.
- If projection stops, the evidence distinguishes display sleep, an
  Android shutdown request and loss of power.

| Code anchor | Purpose |
| --- | --- |
| `firmware/aosp12/bringup/systemui-lockscreen-lifecycle.patch` | Current TV lockscreen lifecycle fix. |
| `tests/aosp12_boot_services.py` | Host coverage for the TV and phone callback cases. |
