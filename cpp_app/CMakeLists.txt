cmake_minimum_required(VERSION 3.10)
project(ServerComputing)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Find packages
find_package(OpenCL REQUIRED)
find_package(PkgConfig QUIET)

if(PkgConfig_FOUND)
    pkg_check_modules(ZMQ libzmq)
endif()

# Include directories
include_directories(${OpenCL_INCLUDE_DIRS})
include_directories(.)

if(ZMQ_FOUND)
    include_directories(${ZMQ_INCLUDE_DIRS})
endif()

# Source files
set(SOURCES
    src/main.cpp
    src/data_io.cpp
    src/opencl_processor.cpp
    src/zmq_comm.cpp
)

set(HEADERS
    src/config.h
    src/types.h
    src/utils.h
    src/data_io.h
    src/opencl_processor.h
    src/zmq_comm.h
)

# Executable
add_executable(main_app ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(main_app
    OpenCL::OpenCL
    zmq
    pthread
)

# Copy kernel file to build directory
configure_file(src/kernels.cl ${CMAKE_CURRENT_BINARY_DIR}/src/kernels.cl COPYONLY)
