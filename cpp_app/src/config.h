// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#ifndef CPP_APP_SRC_CONFIG_H_
#define CPP_APP_SRC_CONFIG_H_

#include <string>

namespace Config {

// ZeroMQ addresses
inline const std::string ZMQ_PUSH_ADDR = "tcp://127.0.0.1:5557";
inline const std::string ZMQ_PULL_ADDR = "tcp://127.0.0.1:5558";

// Output file
inline const std::string OUTPUT_FILE = "../results/output.txt";
}  // namespace Config

#endif  // CPP_APP_SRC_CONFIG_H_
