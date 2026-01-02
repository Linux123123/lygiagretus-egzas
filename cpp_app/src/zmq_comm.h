// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#ifndef CPP_APP_SRC_ZMQ_COMM_H_
#define CPP_APP_SRC_ZMQ_COMM_H_

#include <map>
#include <mutex>
#include <vector>

#include "src/types.h"

/**
 * Sender thread function.
 * Sends server data to Python workers via ZMQ PUSH socket.
 *
 * @param servers Server data to send
 */
void sender_thread(const std::vector<ServerData>& servers);

/**
 * Receiver thread function.
 * Receives stability results from Python workers via ZMQ PULL socket.
 *
 * @param results Output map for results (thread-safe access)
 * @param mutex Mutex for thread-safe result updates
 */
void receiver_thread(
    std::map<int, ServerResult>* results,
    std::mutex* mutex);

#endif  // CPP_APP_SRC_ZMQ_COMM_H_
