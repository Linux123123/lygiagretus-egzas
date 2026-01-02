// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#include "src/zmq_comm.h"

#include <zmq.hpp>

#include <array>
#include <chrono>
#include <cstring>
#include <iostream>
#include <map>
#include <thread>
#include <vector>

#include "src/config.h"
#include "src/utils.h"

void sender_thread(const std::vector<ServerData>& servers) {
    try {
        zmq::context_t ctx(1);
        zmq::socket_t sock(ctx, ZMQ_PUSH);
        sock.connect(Config::ZMQ_PUSH_ADDR);

        std::this_thread::sleep_for(
            std::chrono::milliseconds(Constants::SLEEP_MS));

        // Send all server data
        for (const auto& server : servers) {
            std::array<char, Constants::MSG_SIZE> buf{};
            std::memcpy(buf.data(), &server.id, Constants::ID_SIZE);
            std::memcpy(buf.data() + Constants::ID_SIZE,
                        &server.load, Constants::FLOAT_SIZE);
            std::memcpy(buf.data() + Constants::ID_SIZE + Constants::FLOAT_SIZE,
                        &server.uptime, Constants::UPTIME_SIZE);

            zmq::message_t msg(Constants::MSG_SIZE);
            std::memcpy(msg.data(), buf.data(), Constants::MSG_SIZE);
            sock.send(msg, zmq::send_flags::none);
        }

        // Send stop signal
        zmq::message_t stop(1);
        *static_cast<unsigned char*>(stop.data()) = Constants::STOP_SIGNAL;
        sock.send(stop, zmq::send_flags::none);

        std::cout << Color::YELLOW << "[Sender] " << Color::RESET
                  << "Sent " << servers.size() << " records\n";
    } catch (const std::exception& e) {
        std::cerr << Color::RED << "[Sender] " << e.what()
                  << Color::RESET << "\n";
    }
}

void receiver_thread(
    std::map<int, ServerResult>* results,
    std::mutex* mutex) {
    try {
        zmq::context_t ctx(1);
        zmq::socket_t sock(ctx, ZMQ_PULL);
        sock.bind(Config::ZMQ_PULL_ADDR);

        int count = 0;

        while (true) {
            zmq::message_t msg;
            if (!sock.recv(msg)) {
                continue;
            }

            // Check for stop signal
            if (msg.size() == 1 &&
                *static_cast<unsigned char*>(msg.data()) ==
                    Constants::STOP_SIGNAL) {
                break;
            }

            // Parse result message
            if (msg.size() == Constants::MSG_RESULT_SIZE) {
                int id = 0;
                float stability = 0.0f;

                std::memcpy(&id, msg.data(), Constants::ID_SIZE);
                std::memcpy(&stability,
                            static_cast<char*>(msg.data()) + Constants::ID_SIZE,
                            Constants::FLOAT_SIZE);

                std::scoped_lock lock(*mutex);
                auto it = results->find(id);
                if (it != results->end()) {
                    it->second.stability = stability;
                    it->second.has_python_result = true;
                }
                count++;
            }
        }

        std::cout << Color::MAGENTA << "[Receiver] " << Color::RESET
                  << "Received " << count << " results\n";
    } catch (const std::exception& e) {
        std::cerr << Color::RED << "[Receiver] " << e.what()
                  << Color::RESET << "\n";
    }
}
