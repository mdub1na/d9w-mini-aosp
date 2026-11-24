---
id: B-07
title: "Qualify cold boot and projector safety with SELinux enforcing"
status: open
priority: P0
size: L
stage: daily-base
blocked_by: [B-04]
---

# B-07 — Qualify cold boot and projector safety with SELinux enforcing

The diagnostic AOSP boot reached the interface with airflow and vendor thermal telemetry. Sustained operation, the shutdown path and behavior under enforcing policy still need device evidence. Trace the vendor power, fan and thermal paths before extending test windows. Run from the [private System profile](B-04-reproducible-system-trial.md).

- A cold boot reaches the interface with SELinux enforcing. The test records airflow, light state and the available LED, LCD and TEC telemetry through startup, idle and ordinary shutdown.
- Ordinary shutdown and a controlled fault simulation exercise the intended light-off response. Record the fan behavior and the trigger and timing for each response. Use a simulation that leaves the physical cooling path intact.
- The tester can distinguish display sleep from shutdown using the [remote and power lifecycle checks](B-02-remote-sleep-wake.md). Record enough telemetry to set the duration of later hardware tests.

## Code anchors

| Area | Code |
| --- | --- |
| Board profile and Vendor interface | `firmware/aosp12/device/BoardConfig.mk` |
| Product and policy integration | `firmware/aosp12/device/aosp_d9wmini.mk` |
| TV sleep and wake callbacks | `firmware/aosp12/bringup/systemui-lockscreen-lifecycle.patch` |
