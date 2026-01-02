// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#ifndef CPP_APP_SRC_DATA_IO_H_
#define CPP_APP_SRC_DATA_IO_H_

#include <map>
#include <string>
#include <vector>

#include "src/types.h"

/**
 * Load server data from JSON file.
 * @param filename Path to JSON file
 * @param servers Output vector for server data
 * @param results Output map for server results
 * @return true on success, false on failure
 */
bool load_data(
    const std::string& filename,
    std::vector<ServerData>* servers,
    std::map<int, ServerResult>* results);

/**
 * Write final results to output file.
 * @param servers Original server data (for initial data section)
 * @param results Map of server results
 */
void write_output(
    const std::vector<ServerData>& servers,
    const std::map<int, ServerResult>& results);

#endif  // CPP_APP_SRC_DATA_IO_H_
