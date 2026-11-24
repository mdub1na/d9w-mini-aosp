/* SPDX-License-Identifier: Apache-2.0 */
#include "operation_monitor.h"

#include <string.h>

static bool consume(const char **cursor, const char *literal)
{
    const size_t length = strlen(literal);
    if (strncmp(*cursor, literal, length) != 0)
        return false;
    *cursor += length;
    return true;
}

static bool number(const char **cursor, uint64_t *value)
{
    const char *input = *cursor;
    uint64_t count = 0;
    size_t digits = 0;
    while (input[digits] >= '0' && input[digits] <= '9') {
        if (digits >= 9 || (digits && input[0] == '0'))
            return false;
        count = count * 10 + (uint64_t)(input[digits++] - '0');
    }
    if (!digits)
        return false;
    *cursor += digits;
    *value = count;
    return true;
}

static bool fraction(const char **cursor, uint64_t *completed, uint64_t *total)
{
    return number(cursor, completed) && consume(cursor, "/") && number(cursor, total)
        && *total && *completed <= *total;
}

static enum d9w_status_partition partition(const char **cursor)
{
    if (consume(cursor, "System "))
        return D9W_STATUS_PARTITION_SYSTEM;
    if (consume(cursor, "Data "))
        return D9W_STATUS_PARTITION_DATA;
    return D9W_STATUS_PARTITION_NONE;
}

static int rank(enum d9w_status_phase phase, enum d9w_status_partition target)
{
    switch (phase) {
    case D9W_STATUS_PHASE_VERIFY_SOURCE: return 1;
    case D9W_STATUS_PHASE_WRITE_PARTITION: return target == D9W_STATUS_PARTITION_SYSTEM ? 2 : 3;
    case D9W_STATUS_PHASE_VERIFY_PARTITION: return target == D9W_STATUS_PARTITION_SYSTEM ? 4 : 5;
    default: return 0;
    }
}

static bool advance(struct d9w_operation_monitor *monitor, enum d9w_status_phase phase,
                    enum d9w_status_partition target, struct d9w_status_progress progress)
{
    struct d9w_operation_status *status = &monitor->status;
    const int current = rank(status->phase, status->partition);
    const int next = rank(phase, target);
    if (next < current)
        return false;

    uint64_t *known_total = NULL;
    if (target == D9W_STATUS_PARTITION_SYSTEM)
        known_total = &monitor->system_total;
    else if (target == D9W_STATUS_PARTITION_DATA)
        known_total = &monitor->data_total;
    if (known_total && *known_total) {
        if ((progress.has_total && progress.total != *known_total) || progress.completed > *known_total)
            return false;
        progress.has_total = true;
        progress.total = *known_total;
    }

    const struct d9w_status_progress prior = status->progress;
    if (next == current && prior.unit != D9W_STATUS_UNIT_NONE) {
        if (progress.unit != prior.unit || progress.completed < prior.completed
            || (prior.has_total && (!progress.has_total || progress.total != prior.total)))
            return false;
        if (progress.completed == prior.completed && prior.has_total == progress.has_total)
            return false;
    }
    if (known_total && progress.has_total)
        *known_total = progress.total;
    status->phase = phase;
    status->partition = target;
    status->progress = progress;
    return true;
}

void d9w_monitor_start(struct d9w_operation_monitor *monitor,
                       enum d9w_status_operation operation)
{
    enum d9w_status_phase phase = D9W_STATUS_PHASE_PREFLIGHT;
    if (operation == D9W_STATUS_OP_COLLECT)
        phase = D9W_STATUS_PHASE_COLLECT;
    else if (operation == D9W_STATUS_OP_REBOOT)
        phase = D9W_STATUS_PHASE_REBOOT;
    *monitor = (struct d9w_operation_monitor) {
        .status = {
            .operation = operation,
            .state = D9W_STATUS_STATE_RUNNING,
            .phase = phase,
            .link = D9W_STATUS_LINK_UNOBSERVED,
        },
    };
}

bool d9w_monitor_observe(struct d9w_operation_monitor *monitor, const char *line)
{
    if (monitor->status.state != D9W_STATUS_STATE_RUNNING
        || (monitor->status.operation != D9W_STATUS_OP_INSTALL
            && monitor->status.operation != D9W_STATUS_OP_RESTORE)
        || !consume(&line, "D9W: "))
        return false;

    struct d9w_status_progress progress = {0};
    enum d9w_status_phase phase = D9W_STATUS_PHASE_VERIFY_SOURCE;
    enum d9w_status_partition target = D9W_STATUS_PARTITION_NONE;
    if (consume(&line, "checking AOSP System and clean Data before writing")) {
        return !*line && advance(monitor, phase, target, progress);
    }
    if (consume(&line, "checking all ")) {
        if (!number(&line, &progress.total) || !progress.total
            || !consume(&line, " source files before writing") || *line)
            return false;
        progress.unit = D9W_STATUS_UNIT_ITEMS;
        progress.has_total = true;
    } else if (consume(&line, "source verified ")) {
        if (!fraction(&line, &progress.completed, &progress.total) || *line)
            return false;
        progress.unit = D9W_STATUS_UNIT_ITEMS;
        progress.has_total = true;
    } else if (consume(&line, "zeroed Data through ")) {
        if (!number(&line, &progress.completed) || !consume(&line, " MiB") || *line)
            return false;
        phase = D9W_STATUS_PHASE_WRITE_PARTITION;
        target = D9W_STATUS_PARTITION_DATA;
        progress.unit = D9W_STATUS_UNIT_MIB;
    } else if (consume(&line, "verifying full ")) {
        target = partition(&line);
        if (target == D9W_STATUS_PARTITION_NONE || !consume(&line, "readback") || *line)
            return false;
        phase = D9W_STATUS_PHASE_VERIFY_PARTITION;
        progress.unit = D9W_STATUS_UNIT_MIB;
    } else {
        const bool writing = consume(&line, "written ");
        if (!writing && !consume(&line, "readback "))
            return false;
        target = partition(&line);
        if (target == D9W_STATUS_PARTITION_NONE || !fraction(&line, &progress.completed, &progress.total)
            || !consume(&line, " MiB"))
            return false;
        if (writing) {
            uint64_t item, items;
            if (!consume(&line, " (part ") || !fraction(&line, &item, &items)
                || !item || !consume(&line, ")"))
                return false;
        }
        if (*line)
            return false;
        phase = writing ? D9W_STATUS_PHASE_WRITE_PARTITION : D9W_STATUS_PHASE_VERIFY_PARTITION;
        progress.unit = D9W_STATUS_UNIT_MIB;
        progress.has_total = true;
    }
    return advance(monitor, phase, target, progress);
}
