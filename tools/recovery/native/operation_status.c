/* SPDX-License-Identifier: Apache-2.0 */

#if defined(__APPLE__)
#define _DARWIN_C_SOURCE
#endif
#define _POSIX_C_SOURCE 200809L

#include "operation_status.h"

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define COUNT(array) (sizeof(array) / sizeof((array)[0]))
#define TOKEN(name) "\"" name "\""

static const char *const operations[] = {
    NULL, TOKEN("install"), TOKEN("restore"), TOKEN("collect"), TOKEN("reboot"),
};
static const char *const states[] = {
    TOKEN("waiting"), TOKEN("ready"), TOKEN("blocked"), TOKEN("not_started"),
    TOKEN("awaiting_start"), TOKEN("running"), TOKEN("unknown"), TOKEN("verified"),
    TOKEN("failed"), TOKEN("reboot_requested"),
};
static const char *const phases[] = {
    "null", TOKEN("preflight"), TOKEN("verify_source"), TOKEN("write_partition"),
    TOKEN("verify_partition"), TOKEN("collect"), TOKEN("reboot"),
};
static const char *const partitions[] = {
    "null", TOKEN("system"), TOKEN("data"),
};
static const char *const units[] = {
    NULL, TOKEN("items"), TOKEN("MiB"),
};
static const char *const links[] = {
    TOKEN("unobserved"), TOKEN("connected"), TOKEN("disconnected"),
};

static const char *token(const char *const *table, size_t count, size_t index)
{
    return index < count ? table[index] : NULL;
}

static bool valid_fields(const struct d9w_operation_status *status)
{
    const bool partition_phase = status->phase == D9W_STATUS_PHASE_WRITE_PARTITION ||
                                 status->phase == D9W_STATUS_PHASE_VERIFY_PARTITION;
    if (partition_phase != (status->partition != D9W_STATUS_PARTITION_NONE))
        return false;
    if (status->state <= D9W_STATUS_STATE_AWAITING_START && status->phase != D9W_STATUS_PHASE_NONE)
        return false;
    if (status->state >= D9W_STATUS_STATE_RUNNING && status->state != D9W_STATUS_STATE_UNKNOWN &&
        status->phase == D9W_STATUS_PHASE_NONE)
        return false;
    if (status->state == D9W_STATUS_STATE_REBOOT_REQUESTED &&
        status->phase != D9W_STATUS_PHASE_REBOOT)
        return false;
    if (status->state == D9W_STATUS_STATE_VERIFIED && status->operation == D9W_STATUS_OP_REBOOT)
        return false;
    if (status->phase == D9W_STATUS_PHASE_COLLECT && status->operation != D9W_STATUS_OP_COLLECT)
        return false;
    if (status->phase == D9W_STATUS_PHASE_REBOOT && status->operation != D9W_STATUS_OP_REBOOT)
        return false;
    if ((partition_phase || status->phase == D9W_STATUS_PHASE_VERIFY_SOURCE) &&
        status->operation != D9W_STATUS_OP_INSTALL && status->operation != D9W_STATUS_OP_RESTORE)
        return false;

    const struct d9w_status_progress *progress = &status->progress;
    if (progress->unit == D9W_STATUS_UNIT_NONE)
        return !progress->has_total && progress->completed == 0 && progress->total == 0;
    if (progress->unit == D9W_STATUS_UNIT_ITEMS && status->phase != D9W_STATUS_PHASE_VERIFY_SOURCE)
        return false;
    if (progress->unit == D9W_STATUS_UNIT_MIB && !partition_phase)
        return false;
    if (progress->completed > D9W_OPERATION_STATUS_MAX_COUNTER ||
        progress->total > D9W_OPERATION_STATUS_MAX_COUNTER)
        return false;
    return progress->has_total ? progress->total > 0 && progress->completed <= progress->total
                               : progress->total == 0;
}

bool d9w_status_format(const struct d9w_operation_status *status, char *output,
                       size_t capacity, size_t *written)
{
    if (status == NULL || output == NULL || capacity == 0)
        return false;
    const char *operation = token(operations, COUNT(operations), status->operation);
    const char *state = token(states, COUNT(states), status->state);
    const char *phase = token(phases, COUNT(phases), status->phase);
    const char *partition = token(partitions, COUNT(partitions), status->partition);
    const char *link = token(links, COUNT(links), status->link);
    if (!operation || !state || !phase || !partition || !link || !valid_fields(status))
        return false;

    char progress[112] = "null";
    const struct d9w_status_progress *counter = &status->progress;
    if (counter->unit != D9W_STATUS_UNIT_NONE) {
        const char *unit = token(units, COUNT(units), counter->unit);
        if (unit == NULL)
            return false;
        char total[24] = "null";
        if (counter->has_total)
            (void)snprintf(total, sizeof(total), "%" PRIu64, counter->total);
        const int length = snprintf(progress, sizeof(progress),
            "{\"completed\":%" PRIu64 ",\"total\":%s,\"unit\":%s}", counter->completed, total, unit);
        if (length < 0 || (size_t)length >= sizeof(progress))
            return false;
    }
    const int length = snprintf(output, capacity,
        "{\"version\":1,\"operation\":%s,\"state\":%s,\"phase\":%s,\"partition\":%s,"
        "\"progress\":%s,\"link\":%s}\n", operation, state, phase, partition, progress, link);
    if (length < 0 || (size_t)length >= capacity || length > D9W_OPERATION_STATUS_MAX_BYTES)
        return false;
    if (written != NULL)
        *written = (size_t)length;
    return true;
}

static bool consume(const char **input, const char *expected)
{
    const size_t length = strlen(expected);
    if (strncmp(*input, expected, length) != 0)
        return false;
    *input += length;
    return true;
}

static int read_token(const char **input, const char *const *table, size_t count)
{
    for (size_t i = 0; i < count; ++i)
        if (table[i] != NULL && consume(input, table[i]))
            return (int)i;
    return -1;
}

static bool read_decimal(const char **input, uint64_t *value)
{
    const char *start = *input;
    uint64_t result = 0;
    while (**input >= '0' && **input <= '9') {
        const unsigned digit = (unsigned)(**input - '0');
        if (result > (UINT64_MAX - digit) / 10)
            return false;
        result = result * 10 + digit;
        ++*input;
    }
    if (*input == start || (*start == '0' && *input != start + 1))
        return false;
    *value = result;
    return true;
}

static bool read_progress(const char **input, struct d9w_status_progress *progress)
{
    if (consume(input, "null"))
        return true;
    if (!consume(input, "{\"completed\":") || !read_decimal(input, &progress->completed) ||
        !consume(input, ",\"total\":"))
        return false;
    if (!consume(input, "null")) {
        progress->has_total = true;
        if (!read_decimal(input, &progress->total))
            return false;
    }
    if (!consume(input, ",\"unit\":"))
        return false;
    const int unit = read_token(input, units, COUNT(units));
    if (unit < 0 || !consume(input, "}"))
        return false;
    progress->unit = (enum d9w_status_unit)unit;
    return true;
}

static bool parse(const char *input, size_t size, struct d9w_operation_status *output)
{
    const char *cursor = input;
    int operation, state, phase, partition, link;
    struct d9w_operation_status status = {0};
    if (!consume(&cursor, "{\"version\":1,\"operation\":") ||
        (operation = read_token(&cursor, operations, COUNT(operations))) < 0 ||
        !consume(&cursor, ",\"state\":") || (state = read_token(&cursor, states, COUNT(states))) < 0 ||
        !consume(&cursor, ",\"phase\":") || (phase = read_token(&cursor, phases, COUNT(phases))) < 0 ||
        !consume(&cursor, ",\"partition\":") ||
        (partition = read_token(&cursor, partitions, COUNT(partitions))) < 0 ||
        !consume(&cursor, ",\"progress\":") || !read_progress(&cursor, &status.progress) ||
        !consume(&cursor, ",\"link\":") || (link = read_token(&cursor, links, COUNT(links))) < 0 ||
        !consume(&cursor, "}\n") || (size_t)(cursor - input) != size)
        return false;
    status.operation = (enum d9w_status_operation)operation;
    status.state = (enum d9w_status_state)state;
    status.phase = (enum d9w_status_phase)phase;
    status.partition = (enum d9w_status_partition)partition;
    status.link = (enum d9w_status_link)link;
    if (!valid_fields(&status))
        return false;
    *output = status;
    return true;
}

static bool owner_file(const struct stat *info)
{
    /* An open reader can finish the old snapshot after the publisher replaces it. */
    return S_ISREG(info->st_mode) && (info->st_mode & 07777) == 0600 &&
           info->st_nlink <= 1 && info->st_uid == geteuid();
}

static struct timespec modified(const struct stat *info)
{
#if defined(__APPLE__)
    return info->st_mtimespec;
#else
    return info->st_mtim;
#endif
}

static bool fresh(struct timespec stamp, uint64_t maximum_age_ms)
{
    struct timespec now;
    if (clock_gettime(CLOCK_REALTIME, &now) != 0 || stamp.tv_sec < 0 ||
        now.tv_sec < stamp.tv_sec ||
        (now.tv_sec == stamp.tv_sec && now.tv_nsec < stamp.tv_nsec))
        return false;
    uint64_t seconds = (uint64_t)now.tv_sec - (uint64_t)stamp.tv_sec;
    long nanos = now.tv_nsec - stamp.tv_nsec;
    if (nanos < 0) {
        --seconds;
        nanos += 1000000000L;
    }
    return seconds < maximum_age_ms / 1000 ||
           (seconds == maximum_age_ms / 1000 && nanos <= (long)(maximum_age_ms % 1000) * 1000000L);
}

bool d9w_status_read_at(int dirfd, uint64_t maximum_age_ms, struct d9w_operation_status *output)
{
    if (output == NULL)
        return false;
    const int fd = openat(dirfd, D9W_OPERATION_STATUS_NAME,
                          O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0)
        return false;
    struct stat before, after;
    char data[D9W_OPERATION_STATUS_MAX_BYTES + 1];
    size_t used = 0;
    bool complete = fstat(fd, &before) == 0 && owner_file(&before) &&
                    before.st_size > 0 && before.st_size <= D9W_OPERATION_STATUS_MAX_BYTES;
    while (complete && used < sizeof(data)) {
        const ssize_t count = read(fd, data + used, sizeof(data) - used);
        if (count == 0)
            break;
        if (count > 0)
            used += (size_t)count;
        else if (errno != EINTR)
            complete = false;
    }
    complete = complete && used == (size_t)before.st_size &&
               fstat(fd, &after) == 0 && owner_file(&after) && after.st_size == before.st_size;
    (void)close(fd);
    if (!complete)
        return false;
    const struct timespec initial = modified(&before);
    const struct timespec last = modified(&after);
    if (initial.tv_sec != last.tv_sec || initial.tv_nsec != last.tv_nsec || !fresh(last, maximum_age_ms))
        return false;
    data[used] = '\0';
    return parse(data, used, output);
}

static bool write_bytes(int fd, const char *data, size_t size)
{
    while (size != 0) {
        const ssize_t used = write(fd, data, size);
        if (used < 0 && errno == EINTR)
            continue;
        if (used <= 0)
            return false;
        data += used;
        size -= (size_t)used;
    }
    return true;
}

bool d9w_status_publish_at(int dirfd, const struct d9w_operation_status *status)
{
    char json[D9W_OPERATION_STATUS_MAX_BYTES + 1];
    size_t length;
    if (!d9w_status_format(status, json, sizeof(json), &length))
        return false;
    struct stat existing;
    if (fstatat(dirfd, D9W_OPERATION_STATUS_NAME, &existing, AT_SYMLINK_NOFOLLOW) == 0) {
        if (!owner_file(&existing))
            return false;
    } else if (errno != ENOENT) {
        return false;
    }
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0)
        return false;
    char temporary[80];
    int fd = -1;
    for (unsigned attempt = 0; attempt < 16; ++attempt) {
        const int size = snprintf(temporary, sizeof(temporary), ".d9w-status.%ld.%ld.%u",
                                  (long)getpid(), now.tv_nsec, attempt);
        if (size < 0 || (size_t)size >= sizeof(temporary))
            return false;
        fd = openat(dirfd, temporary, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
        if (fd >= 0)
            break;
        if (errno != EEXIST)
            return false;
    }
    if (fd < 0)
        return false;

    const bool wrote = fchmod(fd, 0600) == 0 && write_bytes(fd, json, length);
    const bool closed = close(fd) == 0;
    if (wrote && closed && renameat(dirfd, temporary, dirfd, D9W_OPERATION_STATUS_NAME) == 0)
        return true;
    (void)unlinkat(dirfd, temporary, 0);
    return false;
}
