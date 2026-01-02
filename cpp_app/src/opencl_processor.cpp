// Copyright 2026 IFF-3-2 Aleksandravicius Linas

#include "src/opencl_processor.h"

#define CL_HPP_TARGET_OPENCL_VERSION 300
#define CL_HPP_MINIMUM_OPENCL_VERSION 120
#include <CL/opencl.hpp>

#include <chrono>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

#include "src/utils.h"

namespace {

cl::Device select_device() {
    std::vector<cl::Platform> platforms;
    cl::Platform::get(&platforms);

    if (platforms.empty()) {
        throw std::runtime_error("No OpenCL platforms found");
    }

    // Try GPU first
    for (const auto& platform : platforms) {
        std::vector<cl::Device> devices;
        platform.getDevices(CL_DEVICE_TYPE_GPU, &devices);
        if (!devices.empty()) {
            std::cout << Color::CYAN << "[OpenCL] " << Color::RESET
                      << platform.getInfo<CL_PLATFORM_NAME>() << " - "
                      << devices[0].getInfo<CL_DEVICE_NAME>() << " (GPU)\n";
            return devices[0];
        }
    }

    // Fall back to CPU
    for (const auto& platform : platforms) {
        std::vector<cl::Device> devices;
        platform.getDevices(CL_DEVICE_TYPE_CPU, &devices);
        if (!devices.empty()) {
            std::cout << Color::CYAN << "[OpenCL] " << Color::RESET
                      << platform.getInfo<CL_PLATFORM_NAME>() << " - "
                      << devices[0].getInfo<CL_DEVICE_NAME>() << " (CPU)\n";
            return devices[0];
        }
    }

    throw std::runtime_error("No OpenCL device found");
}

std::string load_kernel_source() {
    std::ifstream kernel_file("src/kernels.cl");
    if (!kernel_file) {
        throw std::runtime_error("Cannot open kernels.cl");
    }
    return std::string(
        std::istreambuf_iterator<char>(kernel_file),
        std::istreambuf_iterator<char>());
}

}  // namespace

void opencl_thread(
    const std::vector<ServerData>& servers,
    std::map<int, ServerResult>* results,
    std::mutex* mutex) {
    try {
        cl::Device device = select_device();

        cl::Context context(device);

        // Enable profiling + out-of-order execution
        cl_command_queue_properties props =
            CL_QUEUE_PROFILING_ENABLE | CL_QUEUE_OUT_OF_ORDER_EXEC_MODE_ENABLE;
        cl::CommandQueue queue(context, device, props);

        std::string kernel_source = load_kernel_source();
        cl::Program program(context, kernel_source);

        try {
            program.build({device},
                          "-cl-fast-relaxed-math -cl-mad-enable "
                          "-cl-no-signed-zeros");
        } catch (...) {
            std::cerr << "[OpenCL] Build error:\n"
                      << program.getBuildInfo<CL_PROGRAM_BUILD_LOG>(device)
                      << "\n";
            return;
        }

        const int count = static_cast<int>(servers.size());

        std::vector<int> h_uptimes(count), h_ids(count);
        std::vector<float> h_loads(count);

        for (int i = 0; i < count; i++) {
            h_uptimes[i] = servers[i].uptime;
            h_loads[i] = servers[i].load;
            h_ids[i] = servers[i].id;
        }

        cl::Buffer d_uptimes(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                             sizeof(int) * count, h_uptimes.data());
        cl::Buffer d_loads(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                           sizeof(float) * count, h_loads.data());
        cl::Buffer d_ids(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                         sizeof(int) * count, h_ids.data());
        cl::Buffer d_reliability(context, CL_MEM_WRITE_ONLY,
                                 sizeof(float) * count);
        cl::Buffer d_out_ids(context, CL_MEM_WRITE_ONLY,
                             sizeof(int) * count);
        cl::Buffer d_counter(context, CL_MEM_READ_WRITE, sizeof(int));

        int zero = 0;
        queue.enqueueWriteBuffer(d_counter, CL_TRUE, 0, sizeof(int), &zero);

        cl::Kernel kernel(program, "compute_reliability");
        kernel.setArg(0, d_uptimes);
        kernel.setArg(1, d_loads);
        kernel.setArg(2, d_ids);
        kernel.setArg(3, d_reliability);
        kernel.setArg(4, d_out_ids);
        kernel.setArg(Constants::KERNEL_ARG_COUNTER, d_counter);
        kernel.setArg(Constants::KERNEL_ARG_COUNT, count);

        // --- Launch configuration ---
        size_t local_size = 256;
        size_t global_size = ((count + local_size - 1) / local_size) *
                             local_size;

        auto start = std::chrono::high_resolution_clock::now();
        queue.enqueueNDRangeKernel(kernel, cl::NullRange,
                                   cl::NDRange(global_size),
                                   cl::NDRange(local_size));
        queue.finish();
        auto end = std::chrono::high_resolution_clock::now();

        auto duration_ms =
            std::chrono::duration_cast<std::chrono::milliseconds>(
                end - start).count();

        int result_count = 0;
        queue.enqueueReadBuffer(d_counter, CL_TRUE, 0, sizeof(int),
                                &result_count);

        if (result_count > 0) {
            std::vector<float> h_reliability(result_count);
            std::vector<int> h_out_ids(result_count);

            queue.enqueueReadBuffer(d_reliability, CL_TRUE, 0,
                                    sizeof(float) * result_count,
                                    h_reliability.data());
            queue.enqueueReadBuffer(d_out_ids, CL_TRUE, 0,
                                    sizeof(int) * result_count,
                                    h_out_ids.data());

            std::scoped_lock lock(*mutex);
            for (int i = 0; i < result_count; i++) {
                auto it = results->find(h_out_ids[i]);
                if (it != results->end()) {
                    it->second.reliability = h_reliability[i];
                    it->second.has_opencl_result = true;
                }
            }
        }

        std::cout << "[OpenCL] " << result_count << "/" << count
                  << " passed, " << duration_ms << " ms\n";
    } catch (const std::exception& e) {
        std::cerr << "[OpenCL] " << e.what() << "\n";
    }
}
