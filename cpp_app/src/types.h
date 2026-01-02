// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#ifndef CPP_APP_SRC_TYPES_H_
#define CPP_APP_SRC_TYPES_H_

#include <string>

/**
 * Input server data loaded from JSON.
 */
struct ServerData {
    int id;
    std::string location;
    int uptime;
    float load;
};

/**
 * Server result with computed scores.
 */
struct ServerResult {
    int id;
    std::string location;
    int uptime;
    float load;
    float reliability;       // Computed by OpenCL (Filter 1)
    float stability;         // Computed by Python (Filter 2)
    bool has_opencl_result;
    bool has_python_result;
};

#endif  // CPP_APP_SRC_TYPES_H_
