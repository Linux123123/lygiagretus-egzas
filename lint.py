#!/usr/bin/env python3
import subprocess
import sys
import glob
import os

def run_command(command, description):
    print(f"--- Running {description} ---")
    print(f"$ {' '.join(command)}")
    try:
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            print(f"!!! {description} failed with exit code {result.returncode} !!!")
            return False
        print(f">>> {description} passed")
        return True
    except FileNotFoundError:
        print(f"!!! {description} failed: Command not found !!!")
        return False
    except Exception as e:
        print(f"!!! {description} failed: {e} !!!")
        return False

def main():
    success = True

    # Define file groups
    cpp_src_dir = "cpp_app/src"
    cpp_files = glob.glob(os.path.join(cpp_src_dir, "*.cpp"))
    h_files = glob.glob(os.path.join(cpp_src_dir, "*.h"))
    # Combine C++ source and header files
    all_cpp_files = cpp_files + h_files
    
    # Python files
    python_files = []
    python_files.extend(glob.glob("python_app/*.py"))

    print(f"Found {len(all_cpp_files)} C++ files and {len(python_files)} Python files.\n")

    # 1. cpplint
    if all_cpp_files:
        if not run_command(["cpplint"] + all_cpp_files, "cpplint"):
            success = False
        print()

    # 2. clang-tidy
    if all_cpp_files:
        # Ensure build directory exists for compilation database
        if os.path.exists("cpp_app/build/compile_commands.json"):
            if not run_command(["clang-tidy", "-p", "cpp_app/build"] + all_cpp_files, "clang-tidy"):
                success = False
        else:
            print("!!! Skipping clang-tidy: cpp_app/build/compile_commands.json not found !!!")
            print("    Run 'python3 run.py --build' first to generate it.")
            success = False
        print()

    # 3. flake8
    if python_files:
        if not run_command(["flake8"] + python_files, "flake8"):
            success = False
        print()

    # 4. mypy
    if python_files:
        if not run_command(["mypy"] + python_files, "mypy"):
            success = False
        print()

    # 5. pylint
    if python_files:
        if not run_command(["pylint"] + python_files, "pylint"):
            success = False
        print()

    if success:
        print("All linting checks passed!")
        sys.exit(0)
    else:
        print("Some linting checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
