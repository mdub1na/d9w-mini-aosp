/* SPDX-License-Identifier: Apache-2.0 */
#ifndef D9W_OPERATION_MONITOR_H
#define D9W_OPERATION_MONITOR_H

#include "operation_status.h"

struct d9w_operation_monitor {
    struct d9w_operation_status status;
    uint64_t system_total;
    uint64_t data_total;
};

void d9w_monitor_start(struct d9w_operation_monitor *monitor,
                       enum d9w_status_operation operation);
bool d9w_monitor_observe(struct d9w_operation_monitor *monitor, const char *line);

#endif
