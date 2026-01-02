# Parallel Computing System

A distributed computing system using C++ (OpenCL) and Python (multiprocessing) that communicate over ZeroMQ.

## Overview

The system filters server data using two criteria:
- **Filter 1 (C++ OpenCL)**: Computes reliability score, keeps records >= 50
- **Filter 2 (Python)**: Computes stability score, keeps records >= 50

Only records passing both filters appear in the final output.

## Architecture

```
C++ Application                          Python Application
+------------------+                     +------------------+
| Main Thread      |                     | Receiver Process |
|   - Load data    |                     |   - Get from C++ |
|   - Write output |                     +--------+---------+
+--------+---------+                              |
         |                                        v
         +---> OpenCL Thread                 Worker Processes
         |       - GPU/CPU compute           (N-1 CPU cores)
         |       - Filter 1                       |
         |                                        v
         +---> Sender Thread  ---ZMQ--->   Sender Process
         |                                        |
         +---> Receiver Thread <---ZMQ---  Results back
```

## Requirements

### C++
- CMake 3.10+
- OpenCL 1.2+
- ZeroMQ (libzmq)
- nlohmann/json

### Python
- Python 3.10+
- pyzmq

## Build

### C++ Application

```bash
cd cpp_app/build
cmake ..
make
```

### Python Application

```bash
cd python_app
pip install -r requirements.txt
```

## Run

Use the run script to build and launch both applications:

```bash
python run.py 4
```

Options:
- `--half-cpu` - Use half CPU cores for Python workers (when OpenCL runs on CPU)
- `--single-worker` - Use single worker for benchmarking
- `--skip-build` - Skip C++ build step

### Manual Run (alternative)

Terminal 1:
```bash
cd python_app
python main.py
```

Terminal 2:
```bash
cd cpp_app/build
./main_app ../../data/IFF-3-2_AleksandraviciusLinas_L2_dat_4.json
```

## Data Files

| File | Description |
|------|-------------|
| `_dat_1.json` | All records pass both filters |
| `_dat_2.json` | All fail filter 1, some pass filter 2 |
| `_dat_3.json` | All fail filter 2, some pass filter 1 |
| `_dat_4.json` | Mixed results |

## Output

Results are written to `results/output.txt` containing:
- Filter statistics
- Initial data table
- Filtered results with computed reliability and stability scores

## Performance

Measured with 300 records:
- Single worker: ~54 seconds
- Full parallelization: ~10 seconds

## Author
Linas Aleksandravičius
