// SPDX-License-Identifier: Apache-2.0

#include "rapidxml.hpp"

#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <vector>

void rapidxml::parse_error_handler(const char* what, void*) {
    std::fprintf(stderr, "%s\n", what);
    std::abort();
}

int main(int argc, char** argv) {
    assert(argc == 4);
    for (int i = 1; i < argc; ++i) {
        std::ifstream stream(argv[i]);
        assert(stream);
        const std::istreambuf_iterator<char> end;
        std::vector<char> document((std::istreambuf_iterator<char>(stream)), end);
        assert(!document.empty());
        document.push_back('\0');
        rapidxml::xml_document<> parsed;
        parsed.parse<0>(document.data());
        assert(parsed.first_node("recovery"));
    }
}
