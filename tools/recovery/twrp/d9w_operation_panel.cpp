// SPDX-License-Identifier: Apache-2.0

#include "d9w_operation_panel.hpp"
#include "operation_status.h"

#include <fcntl.h>
#include <unistd.h>

namespace d9w {
namespace {

constexpr uint64_t kActiveStatusMaxAgeMs = 8000;
constexpr std::chrono::milliseconds kPollInterval(500);

constexpr const char* kVariables[] = {
    "d9w_panel_operation",
    "d9w_panel_status",
    "d9w_panel_phase",
    "d9w_panel_counter",
    "d9w_panel_percent",
    "d9w_panel_show_bar",
    "d9w_panel_link",
};

std::string GroupedCount(uint64_t value) {
    std::string number = std::to_string(value);
    for (size_t offset = number.size(); offset > 3; offset -= 3)
        number.insert(offset - 3, 1, ',');
    return number;
}

const char* PhaseLabel(const d9w_operation_status& status) {
    switch (status.phase) {
    case D9W_STATUS_PHASE_NONE:
        return "";
    case D9W_STATUS_PHASE_PREFLIGHT:
        return "Checking prerequisites";
    case D9W_STATUS_PHASE_VERIFY_SOURCE:
        return "Verifying source data";
    case D9W_STATUS_PHASE_WRITE_PARTITION:
        return status.partition == D9W_STATUS_PARTITION_SYSTEM ? "Writing System" : "Writing Data";
    case D9W_STATUS_PHASE_VERIFY_PARTITION:
        return status.partition == D9W_STATUS_PARTITION_SYSTEM
            ? "Verifying System readback" : "Verifying Data readback";
    case D9W_STATUS_PHASE_COLLECT:
        return "Collecting logs";
    case D9W_STATUS_PHASE_REBOOT:
        return "Normal boot request";
    }
    return "";
}

}  // namespace

bool OperationPanel::Poll(const char* status_directory, SetValue set_value) {
    const auto now = std::chrono::steady_clock::now();
    if (!needs_refresh_ && now < next_poll_)
        return false;
    next_poll_ = now + kPollInterval;

    d9w_operation_status status{};
    const int directory = open(status_directory, O_RDONLY | O_CLOEXEC | O_DIRECTORY | O_NOFOLLOW);
    const bool have_status = directory >= 0 && d9w_status_read_at(directory, UINT64_MAX, &status);
    if (have_status && (status.state == D9W_STATUS_STATE_RUNNING ||
                        status.state == D9W_STATUS_STATE_AWAITING_START)) {
        // A terminal snapshot remains relevant for this recovery boot. An active snapshot needs a heartbeat.
        if (!d9w_status_read_at(directory, kActiveStatusMaxAgeMs, &status)) {
            status.state = D9W_STATUS_STATE_UNKNOWN;
            status.link = D9W_STATUS_LINK_UNOBSERVED;
        }
    }
    if (directory >= 0)
        close(directory);

    constexpr const char* operations[] = {"Recovery operation", "Install AOSP", "Restore stock",
                                          "Collect logs", "Reboot"};
    constexpr const char* states[] = {"Waiting for recovery", "Ready", "Preflight blocked",
                                      "Operation not started", "Waiting for device start", "In progress",
                                      "Result unknown", "Verified", "Failed", "Reboot requested"};
    constexpr const char* links[] = {"Link unobserved", "Host connected", "Host disconnected"};
    const char* status_label = saw_snapshot_ ? "Result unknown" : "Waiting for status";
    if (have_status)
        status_label = states[status.state];
    saw_snapshot_ |= have_status;

    std::string counter;
    std::string percent = "0";
    bool show_bar = false;
    const auto& progress = status.progress;
    if (progress.unit != D9W_STATUS_UNIT_NONE) {
        const bool running = status.state == D9W_STATUS_STATE_RUNNING;
        counter = running ? "" : "Last reported ";
        counter += GroupedCount(progress.completed);
        if (progress.has_total)
            counter += " / " + GroupedCount(progress.total);
        counter += progress.unit == D9W_STATUS_UNIT_ITEMS ? " items" : " MiB";
        show_bar = running && progress.has_total;
        if (show_bar)
            percent = std::to_string(progress.completed * 100 / progress.total);
    }
    std::array<std::string, 7> values{
        operations[status.operation], status_label, PhaseLabel(status), counter, percent,
        show_bar ? "1" : "0", links[status.link],
    };

    bool changed = false;
    for (size_t i = 0; i < values.size(); ++i) {
        if (needs_refresh_ || values[i] != displayed_[i]) {
            set_value(kVariables[i], values[i].c_str());
            changed = true;
        }
    }
    displayed_.swap(values);
    needs_refresh_ = false;
    return changed;
}

void OperationPanel::Leave() {
    needs_refresh_ = true;
}

}  // namespace d9w
