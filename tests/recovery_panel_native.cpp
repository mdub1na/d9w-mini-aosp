// SPDX-License-Identifier: Apache-2.0

#include "d9w_operation_panel.hpp"
#include "operation_status.h"

#include <cassert>
#include <map>
#include <string>
#include <vector>

#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

namespace {

std::map<std::string, std::string> variables;
std::vector<std::string> updates;

void SetValue(const char* name, const char* value) {
    variables[name] = value;
    updates.push_back(name);
}

void CheckView(const char* status, const char* phase, const char* counter,
               const char* percent, const char* show_bar, const char* link) {
    assert(variables.at("d9w_panel_status") == status);
    assert(variables.at("d9w_panel_phase") == phase);
    assert(variables.at("d9w_panel_counter") == counter);
    assert(variables.at("d9w_panel_percent") == percent);
    assert(variables.at("d9w_panel_show_bar") == show_bar);
    assert(variables.at("d9w_panel_link") == link);
}

void AgeFile(int directory) {
    const struct timespec stamp[] = {{1, 0}, {1, 0}};
    assert(utimensat(directory, D9W_OPERATION_STATUS_NAME, stamp, 0) == 0);
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const char* path = argv[1];
    const int directory = open(path, O_RDONLY | O_DIRECTORY);
    assert(directory >= 0);
    d9w::OperationPanel panel;

    assert(panel.Poll(path, SetValue));
    CheckView("Waiting for status", "", "", "0", "0", "Link unobserved");
    assert(!panel.Poll(path, SetValue));

    d9w_operation_status status{
        D9W_STATUS_OP_INSTALL, D9W_STATUS_STATE_RUNNING, D9W_STATUS_PHASE_VERIFY_PARTITION,
        D9W_STATUS_PARTITION_DATA, {D9W_STATUS_UNIT_MIB, 2048, 4096, true},
        D9W_STATUS_LINK_DISCONNECTED,
    };
    assert(d9w_status_publish_at(directory, &status));
    updates.clear();
    panel.Leave();
    assert(panel.Poll(path, SetValue));
    assert(variables.at("d9w_panel_operation") == "Install AOSP");
    CheckView("In progress", "Verifying Data readback", "2,048 / 4,096 MiB", "50", "1",
              "Host disconnected");
    assert(updates.at(4) == "d9w_panel_percent");
    assert(updates.at(5) == "d9w_panel_show_bar");

    AgeFile(directory);
    panel.Leave();
    assert(panel.Poll(path, SetValue));
    CheckView("Result unknown", "Verifying Data readback", "Last reported 2,048 / 4,096 MiB",
              "0", "0", "Link unobserved");

    status.state = D9W_STATUS_STATE_VERIFIED;
    assert(d9w_status_publish_at(directory, &status));
    AgeFile(directory);
    panel.Leave();
    assert(panel.Poll(path, SetValue));
    CheckView("Verified", "Verifying Data readback", "Last reported 2,048 / 4,096 MiB",
              "0", "0", "Host disconnected");

    status = {D9W_STATUS_OP_RESTORE, D9W_STATUS_STATE_RUNNING, D9W_STATUS_PHASE_VERIFY_SOURCE,
              D9W_STATUS_PARTITION_NONE, {D9W_STATUS_UNIT_ITEMS, 3, 0, false}, D9W_STATUS_LINK_UNOBSERVED};
    assert(d9w_status_publish_at(directory, &status));
    panel.Leave();
    assert(panel.Poll(path, SetValue));
    assert(variables.at("d9w_panel_operation") == "Restore stock");
    CheckView("In progress", "Verifying source data", "3 items", "0", "0", "Link unobserved");

    status = {D9W_STATUS_OP_REBOOT, D9W_STATUS_STATE_REBOOT_REQUESTED, D9W_STATUS_PHASE_REBOOT,
              D9W_STATUS_PARTITION_NONE, {}, D9W_STATUS_LINK_UNOBSERVED};
    assert(d9w_status_publish_at(directory, &status));
    panel.Leave();
    assert(panel.Poll(path, SetValue));
    assert(variables.at("d9w_panel_operation") == "Reboot");
    CheckView("Reboot requested", "Normal boot request", "", "0", "0", "Link unobserved");

    assert(unlinkat(directory, D9W_OPERATION_STATUS_NAME, 0) == 0);
    assert(symlinkat("/dev/null", directory, D9W_OPERATION_STATUS_NAME) == 0);
    panel.Leave();
    assert(panel.Poll(path, SetValue));
    CheckView("Result unknown", "", "", "0", "0", "Link unobserved");
    assert(close(directory) == 0);
}
