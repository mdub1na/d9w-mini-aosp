# Recovery status

The first AOSP 12 trial used an ARM32 System with 64-bit Binder and the stock
kernel and Vendor partition. The test projector reached the Android boot
animation and an interactive UART shell running as `uid=2000(shell)`. It
powered off before reaching the home screen. The shutdown initiator remains
unresolved.

The standard Android command `reboot recovery`, sent through the UART shell,
opened the installed TWRP. TWRP restored stock System and Data from a matched
backup taken on the same projector. The owner confirmed stock Android startup
on screen. The final UART capture was empty.

Repeated USB recovery requests during this failure were unsuccessful. The
tested UART route reaches TWRP while Android init, its serial shell, and the
installed recovery can still run. The hardware test used a CH343-based
ESP32-C3 prototype. [UART bridge source](https://github.com/mdub1na/esp32c3-uart-bridge)

In a later trial, the installed R1 helper accepted a signed System and Data
installation over UART, wrote both partitions and read them back. It also
ran the reboot request and collected first-boot logs without terminal input.
The revised LuatOS bridge read four logcat rotations from R1 and matched the
archived USB copies byte for byte.

The [operation status contract](recovery-operation-status.md) describes the
snapshot shared by the host observer and the
[landscape recovery panel scaffold](recovery-operation-panel.md).
