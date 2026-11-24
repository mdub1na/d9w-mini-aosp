# Recovery operation panel

The panel shows the operation, result, phase, measured progress and observer
link. The R1 landscape theme exposes it in **Advanced → Operation status**.
The Back button and remote Back and Home keys return to the existing menus.

## Local status

The native recovery worker publishes a [version-1 operation snapshot](recovery-operation-status.md)
to `/tmp/d9w-operation-status.json`. It refreshes an active snapshot about once
per second and publishes the terminal result when the local operation finishes.
The R1 publisher reports `Link unobserved` because sending to a UART does not
establish that a host received the data.

The GUI polls from its existing render loop while the panel is selected and
the screen is awake. Reads are limited to one poll per 500 ms. A running phase
with a known total shows a determinate progress bar. A phase with an unknown
total shows the measured count. When the active snapshot exceeds eight seconds
without an update, the panel shows **Result unknown** and keeps the last reported
count as history. A validated terminal snapshot stays visible for that recovery
boot. The panel values are volatile and the display has no effect on recovery
write guards, wake policy or reboot decisions.

## Source integration

The [HDPI page](../tools/recovery/twrp/d9w-operation-panel-hdpi.xml) uses R1's
1920 × 1200 theme coordinates on its 1920 × 1080 framebuffer. It inherits
`RobotoCondensed-Regular.ttf`, `progress_empty` and `progress_full` from the
existing TWRP theme. The [MDPI preview page](../tools/recovery/twrp/d9w-operation-panel.xml)
uses 800 × 480 coordinates for the host adapter.

In an offline copy of the R1 TeamWin recovery source, apply
[`twrp-operation-panel.patch`](../tools/recovery/twrp/twrp-operation-panel.patch)
from that tree's root. Add these source files to the paths named by the patch.

| Files in this repository | TeamWin recovery destination |
| --- | --- |
| `tools/recovery/twrp/d9w_operation_panel.cpp` and `.hpp` | `gui/` |
| `tools/recovery/native/operation_status.c` and `.h` | `gui/` |
| `tools/recovery/twrp/d9w-operation-panel-hdpi.xml` | `gui/theme/landscape_hdpi/` |

In a separate offline copy of the R1 worker source, apply
[`uart-helper-local-status.patch`](../tools/recovery/native/uart-helper-local-status.patch)
in the directory containing `uart-helper.c`. Put `operation_status.c`,
`operation_status.h`, `operation_monitor.c` and `operation_monitor.h` from
`tools/recovery/native/` beside the worker. Compile and link both C files with
its existing sources. The worker and the GUI both open the recovery `/tmp`
directory and use the shared snapshot implementation.

## Host preview and tests

Run the host preview with a version-1 snapshot or create one from recovery
operation output.

```sh
python3 -E -B tools/recovery/progress.py /path/to/r1-operation-output > /tmp/d9w-operation-status.json
python3 -E -B tools/recovery/panel.py /tmp/d9w-operation-status.json
```

The test suite includes a native reader and display fixture. Point
`D9W_TWRP_SOURCE` at the local R1 TeamWin source replay for the additional check
against the original theme, XML parser and build source paths.

```sh
D9W_TWRP_SOURCE=/path/to/r1-teamwin-replay \
  python3 -E -B -m unittest discover -s tests -p 'test_recovery_panel.py' -v
```

These checks cover the source patch and host behavior. Full Android recovery
compilation, framebuffer rendering and hardware navigation require a separate
R1 build and device validation.
