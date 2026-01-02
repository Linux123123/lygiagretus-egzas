#!/usr/bin/env python3
"""
Author: IFF-3-2 Aleksandravicius Linas

Builds and runs both C++ and Python applications together.
"""

import argparse
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

# ANSI color codes
BOLD = "\033[1m"
RESET = "\033[0m"


def get_root() -> Path:
    return Path(__file__).parent.resolve()


def get_executable(root: Path) -> Path:
    if platform.system() == "Windows":
        for subdir in ["Release", "Debug", ""]:
            exe = root / "cpp_app" / "build" / subdir / "main_app.exe"
            if exe.exists():
                return exe
    return root / "cpp_app" / "build" / "main_app"


def build_cpp(root: Path) -> bool:
    build_dir = root / "cpp_app" / "build"

    print("[Build] Building C++...")
    build_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["cmake", ".."],
            cwd=build_dir,
            check=True,
            capture_output=True
        )

        if platform.system() == "Windows":
            subprocess.run(
                ["cmake", "--build", ".", "--config", "Release"],
                cwd=build_dir,
                check=True
            )
        else:
            subprocess.run(["make", "-j4"], cwd=build_dir, check=True)

        print("[Build] Success")
        return True

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[Build] Failed: {e}")
        return False


def stream_output(proc: subprocess.Popen, prefix: str, lock: threading.Lock) -> None:
    for line in iter(proc.stdout.readline, ""):
        if line:
            with lock:
                print(f"{prefix} {line.rstrip()}")
    proc.stdout.close()


def resolve_data_path(root: Path, data_arg: str) -> str:
    if data_arg.isdigit():
        return str(
            root / f"data/IFF-3-2_AleksandraviciusLinas_L2_dat_{data_arg}.json"
        )
    return str(root / data_arg)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run parallel computing applications"
    )
    parser.add_argument(
        "data_file",
        nargs="?",
        default="1",
        help="Dataset number (1-4) or path"
    )
    parser.add_argument(
        "--single-worker",
        action="store_true",
        help="Use single Python worker"
    )
    parser.add_argument(
        "--half-cpu",
        action="store_true",
        help="Use half of CPU cores"
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Force rebuild C++"
    )
    args = parser.parse_args()

    root = get_root()

    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Data: {args.data_file}")
    print()

    # Ensure results directory exists
    (root / "results").mkdir(exist_ok=True)

    # Build C++ if needed
    exe = get_executable(root)
    if args.build or not exe.exists():
        if not build_cpp(root):
            return 1

    # Prepare Python arguments
    py_args = []
    if args.single_worker:
        py_args.append("--single-worker")
    if args.half_cpu:
        py_args.append("--half-cpu")

    data_path = resolve_data_path(root, args.data_file)

    print("[Main] Starting...")
    print()

    # Start Python application
    py_proc = subprocess.Popen(
        [sys.executable, str(root / "python_app" / "main.py")] + py_args,
        cwd=root / "python_app",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    lock = threading.Lock()
    py_thread = threading.Thread(
        target=stream_output,
        args=(py_proc, "[Python]", lock)
    )
    py_thread.start()

    # Wait for Python to initialize
    time.sleep(1)

    if py_proc.poll() is not None:
        print("[Error] Python failed to start")
        return 1

    # Start C++ application
    exe = get_executable(root)
    if not exe.exists():
        print("[Error] C++ executable not found")
        py_proc.terminate()
        return 1

    cpp_proc = subprocess.Popen(
        [str(exe), data_path],
        cwd=root / "cpp_app",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    cpp_thread = threading.Thread(
        target=stream_output,
        args=(cpp_proc, "[C++]", lock)
    )
    cpp_thread.start()

    # Wait for completion
    cpp_proc.wait()
    py_proc.wait()
    py_thread.join()
    cpp_thread.join()

    # Print summary
    print()
    print("=" * 50)
    print(f"Exit: C++={cpp_proc.returncode}, Python={py_proc.returncode}")
    print("=" * 50)

    return cpp_proc.returncode


if __name__ == "__main__":
    sys.exit(main())
