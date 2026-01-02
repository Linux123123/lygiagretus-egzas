// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#ifndef CPP_APP_SRC_OPENCL_PROCESSOR_H_
#define CPP_APP_SRC_OPENCL_PROCESSOR_H_

#include <map>
#include <mutex>
#include <vector>

#include "src/types.h"

/**
 * OpenCL thread function.
 * Computes reliability scores and applies Filter 1 (reliability >= 50).
 *
 * @param servers Input server data
 * @param results Output map for results (thread-safe access)
 * @param mutex Mutex for thread-safe result updates
 */
void opencl_thread(
    const std::vector<ServerData>& servers,
    std::map<int, ServerResult>* results,
    std::mutex* mutex);

#endif  // CPP_APP_SRC_OPENCL_PROCESSOR_H_
