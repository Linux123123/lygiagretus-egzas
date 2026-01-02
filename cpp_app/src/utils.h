// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#ifndef CPP_APP_SRC_UTILS_H_
#define CPP_APP_SRC_UTILS_H_

namespace Color {

constexpr const char* RESET   = "\033[0m";
constexpr const char* RED     = "\033[31m";
constexpr const char* GREEN   = "\033[32m";
constexpr const char* YELLOW  = "\033[33m";
constexpr const char* BLUE    = "\033[34m";
constexpr const char* MAGENTA = "\033[35m";
constexpr const char* CYAN    = "\033[36m";
constexpr const char* BOLD    = "\033[1m";

}  // namespace Color

namespace Constants {

// Message sizes for ZMQ binary protocol
constexpr int MSG_SIZE = 12;         // id(4) + load(4) + uptime(4)
constexpr int MSG_RESULT_SIZE = 8;   // id(4) + stability(4)
constexpr int ID_SIZE = 4;
constexpr int FLOAT_SIZE = 4;
constexpr int UPTIME_SIZE = 4;

// Timing
constexpr int SLEEP_MS = 500;

// Protocol
constexpr unsigned char STOP_SIGNAL = 0xFF;

// OpenCL kernel arguments
constexpr int KERNEL_ARG_COUNTER = 5;
constexpr int KERNEL_ARG_COUNT = 6;

// Output formatting
constexpr int LINE_WIDTH = 80;
constexpr int COL_ID = 6;
constexpr int COL_LOC = 16;
constexpr int COL_UPTIME = 10;
constexpr int COL_LOAD = 10;
constexpr int COL_REL = 14;
constexpr int COL_STAB = 14;

}  // namespace Constants

#endif  // CPP_APP_SRC_UTILS_H_
