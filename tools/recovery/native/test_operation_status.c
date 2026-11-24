/* SPDX-License-Identifier: Apache-2.0 */

#if defined(__APPLE__)
#define _DARWIN_C_SOURCE
#endif
#define _POSIX_C_SOURCE 200809L

#include "operation_status.h"

#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

static const struct d9w_operation_status writing = {
    .operation = D9W_STATUS_OP_INSTALL,
    .state = D9W_STATUS_STATE_RUNNING,
    .phase = D9W_STATUS_PHASE_VERIFY_PARTITION,
    .partition = D9W_STATUS_PARTITION_DATA,
    .progress = {
        .unit = D9W_STATUS_UNIT_MIB,
        .completed = 2048,
        .total = 4096,
        .has_total = true,
    },
    .link = D9W_STATUS_LINK_UNOBSERVED,
};

static const char expected[] =
    "{\"version\":1,\"operation\":\"install\",\"state\":\"running\","
    "\"phase\":\"verify_partition\",\"partition\":\"data\","
    "\"progress\":{\"completed\":2048,\"total\":4096,\"unit\":\"MiB\"},"
    "\"link\":\"unobserved\"}\n";

static void put_bytes(int dirfd, const char *bytes, size_t size, mode_t mode)
{
    const int file = openat(dirfd, D9W_OPERATION_STATUS_NAME,
                            O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW, 0600);
    assert(file >= 0);
    assert(write(file, bytes, size) == (ssize_t)size);
    assert(fchmod(file, mode) == 0);
    assert(close(file) == 0);
}

static void requires_rejection(int dirfd)
{
    struct d9w_operation_status output = writing;
    assert(!d9w_status_read_at(dirfd, 2000, &output));
    assert(output.state == D9W_STATUS_STATE_RUNNING && output.progress.completed == 2048);
}

static void test_format(void)
{
    char json[D9W_OPERATION_STATUS_MAX_BYTES + 1];
    size_t size;
    assert(d9w_status_format(&writing, json, sizeof(json), &size));
    assert(size == sizeof(expected) - 1 && strcmp(json, expected) == 0);
    assert(!d9w_status_format(&writing, json, size, NULL));

    struct d9w_operation_status invalid = writing;
    invalid.progress.total = 2047;
    assert(!d9w_status_format(&invalid, json, sizeof(json), NULL));
    invalid = writing;
    invalid.partition = D9W_STATUS_PARTITION_NONE;
    assert(!d9w_status_format(&invalid, json, sizeof(json), NULL));
    invalid = writing;
    invalid.progress.unit = D9W_STATUS_UNIT_ITEMS;
    assert(!d9w_status_format(&invalid, json, sizeof(json), NULL));
    invalid = writing;
    invalid.operation = D9W_STATUS_OP_COLLECT;
    assert(!d9w_status_format(&invalid, json, sizeof(json), NULL));
    invalid = writing;
    invalid.state = D9W_STATUS_STATE_REBOOT_REQUESTED;
    assert(!d9w_status_format(&invalid, json, sizeof(json), NULL));

    struct d9w_operation_status source = {
        .operation = D9W_STATUS_OP_RESTORE,
        .state = D9W_STATUS_STATE_RUNNING,
        .phase = D9W_STATUS_PHASE_VERIFY_SOURCE,
        .progress = {.unit = D9W_STATUS_UNIT_ITEMS, .completed = 4},
        .link = D9W_STATUS_LINK_UNOBSERVED,
    };
    assert(d9w_status_format(&source, json, sizeof(json), NULL) &&
           strstr(json, "\"progress\":{\"completed\":4,\"total\":null,\"unit\":\"items\"}"));
    source.progress.completed = D9W_OPERATION_STATUS_MAX_COUNTER;
    assert(d9w_status_format(&source, json, sizeof(json), NULL));
    ++source.progress.completed;
    assert(!d9w_status_format(&source, json, sizeof(json), NULL));
}

static void test_publish_and_read(int dirfd)
{
    requires_rejection(dirfd);
    const mode_t previous_mask = umask(0777);
    assert(d9w_status_publish_at(dirfd, &writing));
    (void)umask(previous_mask);

    struct d9w_operation_status output;
    assert(d9w_status_read_at(dirfd, 2000, &output));
    assert(output.operation == writing.operation && output.state == writing.state &&
           output.phase == writing.phase && output.partition == writing.partition);
    assert(output.progress.unit == D9W_STATUS_UNIT_MIB && output.progress.has_total &&
           output.progress.completed == 2048 && output.progress.total == 4096 &&
           output.link == D9W_STATUS_LINK_UNOBSERVED);
    struct d9w_operation_status terminal = writing;
    terminal.state = D9W_STATUS_STATE_VERIFIED;
    terminal.progress.completed = 4096;
    assert(d9w_status_publish_at(dirfd, &terminal));
    assert(d9w_status_read_at(dirfd, 2000, &output) && output.state == D9W_STATUS_STATE_VERIFIED);

    const struct d9w_operation_status reboot = {
        .operation = D9W_STATUS_OP_REBOOT,
        .state = D9W_STATUS_STATE_REBOOT_REQUESTED,
        .phase = D9W_STATUS_PHASE_REBOOT,
    };
    assert(d9w_status_publish_at(dirfd, &reboot));
    assert(d9w_status_read_at(dirfd, 2000, &output) &&
           output.state == D9W_STATUS_STATE_REBOOT_REQUESTED &&
           output.progress.unit == D9W_STATUS_UNIT_NONE && output.link == D9W_STATUS_LINK_UNOBSERVED);

    terminal.progress.completed = 4097;
    assert(!d9w_status_publish_at(dirfd, &terminal));
    assert(d9w_status_read_at(dirfd, 2000, &output) &&
           output.state == D9W_STATUS_STATE_REBOOT_REQUESTED);
}

static void test_rejected_files(int dirfd)
{
    put_bytes(dirfd, expected, sizeof(expected) - 1, 0644);
    requires_rejection(dirfd);
    assert(!d9w_status_publish_at(dirfd, &writing));

    put_bytes(dirfd, expected, sizeof(expected) - 1, 0600);
    const time_t now = time(NULL);
    assert(now > 60);
    struct timespec stamps[2] = {{now - 60, 0}, {now - 60, 0}};
    assert(utimensat(dirfd, D9W_OPERATION_STATUS_NAME, stamps, 0) == 0);
    requires_rejection(dirfd);
    stamps[1].tv_sec = now + 60;
    assert(utimensat(dirfd, D9W_OPERATION_STATUS_NAME, stamps, 0) == 0);
    requires_rejection(dirfd);

    char too_long[D9W_OPERATION_STATUS_MAX_BYTES + 1];
    memset(too_long, 'a', sizeof(too_long));
    put_bytes(dirfd, too_long, sizeof(too_long), 0600);
    requires_rejection(dirfd);
    put_bytes(dirfd, expected, sizeof(expected), 0600); /* Trailing NUL is not canonical JSON. */
    requires_rejection(dirfd);
    put_bytes(dirfd, expected, sizeof(expected) - 5, 0600);
    requires_rejection(dirfd);

    static const char overflow[] =
        "{\"version\":1,\"operation\":\"install\",\"state\":\"running\","
        "\"phase\":\"verify_source\",\"partition\":null,"
        "\"progress\":{\"completed\":18446744073709551616,\"total\":null,\"unit\":\"items\"},"
        "\"link\":\"unobserved\"}\n";
    put_bytes(dirfd, overflow, sizeof(overflow) - 1, 0600);
    requires_rejection(dirfd);

    static const char beyond_bound[] =
        "{\"version\":1,\"operation\":\"install\",\"state\":\"running\","
        "\"phase\":\"verify_source\",\"partition\":null,"
        "\"progress\":{\"completed\":4,\"total\":1000000000,\"unit\":\"items\"},"
        "\"link\":\"unobserved\"}\n";
    put_bytes(dirfd, beyond_bound, sizeof(beyond_bound) - 1, 0600);
    requires_rejection(dirfd);
}

static void test_links_and_fifo(int dirfd)
{
    assert(unlinkat(dirfd, D9W_OPERATION_STATUS_NAME, 0) == 0);
    assert(mkfifoat(dirfd, D9W_OPERATION_STATUS_NAME, 0600) == 0);
    requires_rejection(dirfd);
    assert(!d9w_status_publish_at(dirfd, &writing));
    assert(unlinkat(dirfd, D9W_OPERATION_STATUS_NAME, 0) == 0);

    assert(d9w_status_publish_at(dirfd, &writing));
    assert(linkat(dirfd, D9W_OPERATION_STATUS_NAME, dirfd, "receipt.json", 0) == 0);
    requires_rejection(dirfd);
    assert(!d9w_status_publish_at(dirfd, &writing));
    assert(unlinkat(dirfd, D9W_OPERATION_STATUS_NAME, 0) == 0);
    assert(symlinkat("receipt.json", dirfd, D9W_OPERATION_STATUS_NAME) == 0);
    requires_rejection(dirfd);
    assert(!d9w_status_publish_at(dirfd, &writing));
    assert(unlinkat(dirfd, D9W_OPERATION_STATUS_NAME, 0) == 0);
    assert(unlinkat(dirfd, "receipt.json", 0) == 0);
}

int main(void)
{
    char directory[] = "/tmp/d9w-operation-status-test.XXXXXX";
    assert(mkdtemp(directory) != NULL);
    const int dirfd = open(directory, O_DIRECTORY | O_RDONLY | O_NOFOLLOW);
    assert(dirfd >= 0);
    test_format();
    test_publish_and_read(dirfd);
    test_rejected_files(dirfd);
    test_links_and_fifo(dirfd);
    assert(close(dirfd) == 0);
    assert(rmdir(directory) == 0);
    puts("Recovery operation status fixtures passed.");
    return 0;
}
