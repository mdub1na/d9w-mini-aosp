# Recovery operation panel

The [landscape page](../tools/recovery/twrp/d9w-operation-panel.xml) shows the
operation, current result, phase, available measurement and observer link.
The host adapter projects a [version-1 status snapshot](recovery-operation-status.md)
into the page's DataManager variables.

```sh
python3 -E -B tools/recovery/progress.py /path/to/r1-operation-output > /tmp/d9w-operation-status.json
python3 -E -B tools/recovery/panel.py /tmp/d9w-operation-status.json
```

A running phase with a known total displays a determinate progress bar. With
an unknown total, the panel displays the measured count. A terminal or unknown
result displays the last count as history. Link state is displayed separately,
so a future device-side producer can report local work even when its host has
disconnected.

## Theme contract

The page uses the installed landscape theme's 800 × 480 design coordinate
space and standard TWRP `background`, `fill`, `text` and `progressbar`
widgets. It references the theme's `RobotoCondensed-Regular.ttf`,
`progress_empty` and `progress_full` resources. The headless tests check the
mapped fields and the XML interface.

For a future recovery build, include `d9w-operation-panel.xml` alongside the
landscape `ui.xml` through its existing `include/xmlfile` list. Register
`d9w_operation_status` as a status destination and keep normal recovery
navigation available. Apply the namespaced variables to DataManager from the
GUI thread after each complete local snapshot. Assign the bar visibility
after its percentage. The panel's initial variables display a waiting state
before the first snapshot.

This source scaffold has host checks. A native snapshot publisher, page
routing and framebuffer validation belong to the device integration. The
page contains display widgets only. Firmware writes, wake and reboot behavior,
and recovery interlocks stay with their existing owners.

```sh
python3 -E -B -m unittest discover -s tests -p 'test_recovery_*.py' -v
```
