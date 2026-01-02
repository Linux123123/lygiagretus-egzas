// Copyright 2026 IFF-3-2 Aleksandravicius Linas

/**
 * OpenCL: reliability calculation + Filter 1 (reliability >= 50)
 * Communication with Python via ZeroMQ binary protocol
 *
 * Performance measurements (300 records):
 * - Single worker (Python) + OpenCL: ~54 seconds
 * - Full parallelization (Python N-1) + OpenCL: ~10 seconds
 * - Single worker OpenCL: Not available due to AMD driver limitations
 */

#include <chrono>
#include <iostream>
#include <map>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#include "src/data_io.h"
#include "src/opencl_processor.h"
#include "src/types.h"
#include "src/utils.h"
#include "src/zmq_comm.h"

namespace {

std::string parse_input_file(int argc, char* argv[]) {
    std::string input = "../data/IFF-3-2_AleksandraviciusLinas_L2_dat_1.json";
    for (int i = 1; i < argc; i++) {
        if (argv[i][0] != '-') {
            input = argv[i];
        }
    }
    return input;
}

}  // namespace

int main(int argc, char* argv[]) {
    std::cout.setf(std::ios::unitbuf);
    std::cout << Color::BOLD << "\n=== C++ Application ==="
              << Color::RESET << "\n";

    const std::string input_file = parse_input_file(argc, argv);
    std::cout << Color::BLUE << "[Main] " << Color::RESET
              << "Input: " << input_file << "\n";

    // Shared data structures
    std::vector<ServerData> servers;
    std::map<int, ServerResult> results;
    std::mutex results_mutex;

    // Load data
    if (!load_data(input_file, &servers, &results)) {
        return 1;
    }
    if (servers.empty()) {
        std::cerr << Color::RED << "[Error] No data" << Color::RESET << "\n";
        return 1;
    }

    auto start = std::chrono::high_resolution_clock::now();

    {
        std::jthread t_opencl(opencl_thread,
                              std::cref(servers),
                              &results,
                              &results_mutex);
        std::jthread t_sender(sender_thread, std::cref(servers));
        std::jthread t_receiver(receiver_thread,
                                &results,
                                &results_mutex);
    }  // All threads auto-join here

    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::high_resolution_clock::now() - start).count();

    // Write output
    write_output(servers, results);

    std::cout << Color::BOLD << "\n[Main] Total: " << elapsed << "s"
              << Color::RESET << "\n";

    return 0;
}
