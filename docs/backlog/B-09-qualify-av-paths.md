---
id: B-09
title: "Qualify HDMI input, audio and hardware video decoding"
status: open
priority: P1
size: L
stage: hardware
blocked_by: [B-04]
---

# B-09 — Qualify HDMI input, audio and hardware video decoding

The first AOSP trial displayed its own interface. HDMI input, audio routing and the choice of hardware decoder need separate evidence. Check these paths on the [private System profile](B-04-reproducible-system-trial.md). Use short tests before [projector safety](B-07-qualify-projection-safety.md) is qualified.

- Select HDMI from the TV interface and play a known input with picture and sound. Unplug and reconnect the input, then return to Android and check the selected audio route and volume control.
- Play locally owned test clips with recorded resolutions and codecs. Confirm picture, audio and seeking, and name the active decoder and its hardware or software class from Android media evidence. Record the unsupported formats separately from the successful cases.

## Code anchors

| Area | Code |
| --- | --- |
| TV product configuration | `firmware/aosp12/device/aosp_d9wmini.mk` |
| Media and display Vendor interface boundary | `firmware/aosp12/device/BoardConfig.mk` |
