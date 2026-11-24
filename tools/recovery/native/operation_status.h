/* SPDX-License-Identifier: Apache-2.0 */

#ifndef D9W_OPERATION_STATUS_H
#define D9W_OPERATION_STATUS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define D9W_OPERATION_STATUS_NAME "d9w-operation-status.json"
#define D9W_OPERATION_STATUS_MAX_BYTES 384
#define D9W_OPERATION_STATUS_MAX_COUNTER UINT64_C(999999999)

enum d9w_status_operation {
    D9W_STATUS_OP_NONE,
    D9W_STATUS_OP_INSTALL,
    D9W_STATUS_OP_RESTORE,
    D9W_STATUS_OP_COLLECT,
    D9W_STATUS_OP_REBOOT,
};

enum d9w_status_state {
    D9W_STATUS_STATE_WAITING,
    D9W_STATUS_STATE_READY,
    D9W_STATUS_STATE_BLOCKED,
    D9W_STATUS_STATE_NOT_STARTED,
    D9W_STATUS_STATE_AWAITING_START,
    D9W_STATUS_STATE_RUNNING,
    D9W_STATUS_STATE_UNKNOWN,
    D9W_STATUS_STATE_VERIFIED,
    D9W_STATUS_STATE_FAILED,
    D9W_STATUS_STATE_REBOOT_REQUESTED,
};

enum d9w_status_phase {
    D9W_STATUS_PHASE_NONE,
    D9W_STATUS_PHASE_PREFLIGHT,
    D9W_STATUS_PHASE_VERIFY_SOURCE,
    D9W_STATUS_PHASE_WRITE_PARTITION,
    D9W_STATUS_PHASE_VERIFY_PARTITION,
    D9W_STATUS_PHASE_COLLECT,
    D9W_STATUS_PHASE_REBOOT,
};

enum d9w_status_partition {
    D9W_STATUS_PARTITION_NONE,
    D9W_STATUS_PARTITION_SYSTEM,
    D9W_STATUS_PARTITION_DATA,
};

enum d9w_status_unit {
    D9W_STATUS_UNIT_NONE,
    D9W_STATUS_UNIT_ITEMS,
    D9W_STATUS_UNIT_MIB,
};

enum d9w_status_link {
    D9W_STATUS_LINK_UNOBSERVED,
    D9W_STATUS_LINK_CONNECTED,
    D9W_STATUS_LINK_DISCONNECTED,
};

struct d9w_status_progress {
    enum d9w_status_unit unit;
    uint64_t completed;
    uint64_t total;
    bool has_total;
};

struct d9w_operation_status {
    enum d9w_status_operation operation;
    enum d9w_status_state state;
    enum d9w_status_phase phase;
    enum d9w_status_partition partition;
    struct d9w_status_progress progress;
    enum d9w_status_link link;
};

/* Emit the canonical version-1 encoding and length excluding its C terminator. */
bool d9w_status_format(const struct d9w_operation_status *status, char *output,
                       size_t capacity, size_t *written);

/* Update volatile status atomically within the caller's trusted directory. */
bool d9w_status_publish_at(int dirfd, const struct d9w_operation_status *status);

/* Read only a fresh, canonical, owner-private regular file. Failure leaves output intact. */
bool d9w_status_read_at(int dirfd, uint64_t maximum_age_ms, struct d9w_operation_status *output);

#ifdef __cplusplus
}
#endif

#endif
