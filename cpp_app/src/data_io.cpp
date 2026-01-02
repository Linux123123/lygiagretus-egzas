// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#include "src/data_io.h"

#include <filesystem>  // NOLINT(build/c++17)
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>

#include "src/config.h"
#include "src/utils.h"

using json = nlohmann::json;

bool load_data(
    const std::string& filename,
    std::vector<ServerData>* servers,
    std::map<int, ServerResult>* results) {
    std::ifstream file(filename);
    if (!file) {
        std::cerr << Color::RED << "[Error] Cannot open: " << filename
                  << Color::RESET << "\n";
        return false;
    }

    try {
        json json_data;
        file >> json_data;

        for (const auto& server : json_data["servers"]) {
            ServerData data{
                .id = server["id"],
                .location = server["location"],
                .uptime = server["uptime"],
                .load = server["load"]
            };
            servers->push_back(data);

            (*results)[data.id] = ServerResult{
                .id = data.id,
                .location = data.location,
                .uptime = data.uptime,
                .load = data.load,
                .reliability = 0.0f,
                .stability = 0.0f,
                .has_opencl_result = false,
                .has_python_result = false
            };
        }

        std::cout << Color::GREEN << "[Data] " << Color::RESET
                  << "Loaded " << servers->size() << " servers\n";
        return true;
    } catch (const std::exception& e) {
        std::cerr << Color::RED << "[Error] JSON: " << e.what()
                  << Color::RESET << "\n";
        return false;
    }
}

void write_output(
    const std::vector<ServerData>& servers,
    const std::map<int, ServerResult>& results
) {
    std::filesystem::create_directories("../results");
    std::ofstream file(Config::OUTPUT_FILE);

    if (!file) {
        std::cerr << Color::RED << "[Error] Cannot create output\n"
                  << Color::RESET;
        return;
    }

    // Calculate statistics
    int opencl_passed = 0;
    int python_passed = 0;
    int both_passed = 0;

    for (const auto& [id, result] : results) {
        if (result.has_opencl_result) {
            opencl_passed++;
        }
        if (result.has_python_result) {
            python_passed++;
        }
        if (result.has_opencl_result && result.has_python_result) {
            both_passed++;
        }
    }

    int total_servers = static_cast<int>(servers.size());

    // Write header
    file << std::string(Constants::LINE_WIDTH, '=') << "\n"
         << "STATISTICS:\n"
         << "  Total: " << total_servers
         << ", Filter1: " << opencl_passed
         << ", Filter2: " << python_passed
         << ", Both: " << both_passed << "\n\n";

    // Write initial data section
    file << std::string(Constants::LINE_WIDTH, '=') << "\n"
         << "INITIAL DATA\n"
         << std::string(Constants::LINE_WIDTH, '-') << "\n"
         << std::left
         << std::setw(Constants::COL_ID) << "ID"
         << std::setw(Constants::COL_LOC) << "Location"
         << std::setw(Constants::COL_UPTIME) << "Uptime"
         << std::setw(Constants::COL_LOAD) << "Load" << "\n"
         << std::string(Constants::LINE_WIDTH, '-') << "\n";

    for (const auto& server : servers) {
        file << std::left
             << std::setw(Constants::COL_ID) << server.id
             << std::setw(Constants::COL_LOC) << server.location
             << std::setw(Constants::COL_UPTIME) << server.uptime
             << std::fixed << std::setprecision(2)
             << std::setw(Constants::COL_LOAD) << server.load << "\n";
    }

    // Write filtered results section
    file << "\n" << std::string(Constants::LINE_WIDTH, '=') << "\n"
         << "FILTERED RESULTS (passed both filters)\n"
         << std::string(Constants::LINE_WIDTH, '-') << "\n"
         << std::left
         << std::setw(Constants::COL_ID) << "ID"
         << std::setw(Constants::COL_LOC) << "Location"
         << std::setw(Constants::COL_UPTIME) << "Uptime"
         << std::setw(Constants::COL_LOAD) << "Load"
         << std::setw(Constants::COL_REL) << "Reliability"
         << std::setw(Constants::COL_STAB) << "Stability" << "\n"
         << std::string(Constants::LINE_WIDTH, '-') << "\n";

    // Write filtered data rows
    for (const auto& [id, result] : results) {
        if (result.has_opencl_result && result.has_python_result) {
            file << std::left
                 << std::setw(Constants::COL_ID) << result.id
                 << std::setw(Constants::COL_LOC) << result.location
                 << std::setw(Constants::COL_UPTIME) << result.uptime
                 << std::fixed << std::setprecision(2)
                 << std::setw(Constants::COL_LOAD) << result.load
                 << std::setprecision(4)
                 << std::setw(Constants::COL_REL) << result.reliability
                 << std::setw(Constants::COL_STAB) << result.stability << "\n";
        }
    }

    file << std::string(Constants::LINE_WIDTH, '=') << "\n";

    std::cout << Color::GREEN << "[Output] " << Color::RESET
              << both_passed << " records -> " << Config::OUTPUT_FILE << "\n";
}
