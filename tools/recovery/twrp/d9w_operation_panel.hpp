// SPDX-License-Identifier: Apache-2.0

#ifndef D9W_OPERATION_PANEL_HPP
#define D9W_OPERATION_PANEL_HPP

#include <array>
#include <chrono>
#include <string>

namespace d9w {

class OperationPanel {
public:
    using SetValue = void (*)(const char* name, const char* value);

    bool Poll(const char* status_directory, SetValue set_value);
    void Leave();

private:
    std::chrono::steady_clock::time_point next_poll_{};
    std::array<std::string, 7> displayed_{};
    bool needs_refresh_ = true;
    bool saw_snapshot_ = false;
};

}  // namespace d9w

#endif
