/* SPDX-License-Identifier: Apache-2.0 */
#include "operation_monitor.h"

#include <assert.h>

int main(void)
{
    struct d9w_operation_monitor monitor;
    d9w_monitor_start(&monitor, D9W_STATUS_OP_INSTALL);
    assert(monitor.status.phase == D9W_STATUS_PHASE_PREFLIGHT);
    assert(d9w_monitor_observe(&monitor, "D9W: source verified 33/33"));
    assert(!d9w_monitor_observe(&monitor, "D9W: source verified 33/33"));
    assert(!d9w_monitor_observe(&monitor, "D9W: source verified 33/34"));
    assert(!d9w_monitor_observe(&monitor, "D9W: source verified 032/33"));
    assert(d9w_monitor_observe(&monitor, "D9W: written System 1776/1776 MiB (part 1/33)"));
    assert(d9w_monitor_observe(&monitor, "D9W: written Data 1024/27467 MiB (part 2/33)"));
    assert(d9w_monitor_observe(&monitor, "D9W: zeroed Data through 2048 MiB"));
    assert(monitor.status.progress.total == 27467 && monitor.status.progress.has_total);
    assert(!d9w_monitor_observe(&monitor, "D9W: zeroed Data through 27468 MiB"));
    assert(d9w_monitor_observe(&monitor, "D9W: verifying full System readback"));
    assert(monitor.status.phase == D9W_STATUS_PHASE_VERIFY_PARTITION);
    assert(monitor.status.progress.total == 1776 && monitor.status.progress.completed == 0);
    assert(!d9w_monitor_observe(&monitor, "D9W: written Data 27467/27467 MiB (part 33/33)"));
    assert(d9w_monitor_observe(&monitor, "D9W: readback Data 26624/27467 MiB"));
    assert(!d9w_monitor_observe(&monitor, "D9W: readback Data 26625/27468 MiB"));
    assert(!d9w_monitor_observe(&monitor, "D9W: AOSP SYSTEM AND DATA VERIFIED (valid_receipt)"));
    assert(monitor.status.state == D9W_STATUS_STATE_RUNNING);
    assert(monitor.status.progress.completed == 26624);

    d9w_monitor_start(&monitor, D9W_STATUS_OP_RESTORE);
    assert(d9w_monitor_observe(&monitor, "D9W: checking all 28 source files before writing"));
    assert(monitor.status.progress.unit == D9W_STATUS_UNIT_ITEMS && monitor.status.progress.total == 28);
    assert(d9w_monitor_observe(&monitor, "D9W: zeroed Data through 2 MiB"));
    assert(!monitor.status.progress.has_total);
    assert(d9w_monitor_observe(&monitor, "D9W: readback Data 4/16 MiB"));

    d9w_monitor_start(&monitor, D9W_STATUS_OP_REBOOT);
    assert(monitor.status.phase == D9W_STATUS_PHASE_REBOOT);
    assert(!d9w_monitor_observe(&monitor, "D9W: written Data 1/2 MiB (part 1/1)"));
    return 0;
}
