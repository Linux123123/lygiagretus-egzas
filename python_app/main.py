#!/usr/bin/env python3
"""
Python Worker Application server stability computation.
Author: IFF-3-2 Aleksandravicius Linas

Computes stability scores (Filter 2) using multiprocessing.
Communicates with C++ application via ZeroMQ.

Architecture:
- Receiver process: receives data from C++ via ZMQ
- Worker processes: compute stability scores (N-1 CPU cores)
- Sender process: sends filtered results back to C++

Performance (300 records):
- Single worker: ~54 seconds
- Full parallelization: ~10 seconds
"""

import sys
import time
from multiprocessing import Process, Queue, Value

from colors import Color
from config import STABILITY_ITERATIONS, get_worker_count
from processes import receiver_process, sender_process, worker_process


def parse_args() -> int:
    """Parse command line arguments."""
    use_half_cpu = "--half-cpu" in sys.argv
    single_worker = "--single-worker" in sys.argv

    if single_worker:
        return 1
    return get_worker_count(use_half_cpu)


def main() -> None:
    """Main entry point."""
    print(
        f"{Color.BOLD}\n=== Python Worker Application ==={Color.RESET}",
        flush=True
    )

    num_workers = parse_args()

    print(
        f"{Color.BLUE}[Main]{Color.RESET} Workers: {num_workers}, "
        f"Iterations: {STABILITY_ITERATIONS:,}",
        flush=True
    )

    # Create communication queues
    task_queue: Queue = Queue()
    result_queue: Queue = Queue()

    # Shared values for statistics
    total_received = Value('i', 0)
    total_passed = Value('i', 0)

    start_time = time.perf_counter()

    # Start receiver process
    p_receiver = Process(
        target=receiver_process,
        args=(task_queue, num_workers, total_received),
        name="Receiver"
    )
    p_receiver.start()

    # Start worker processes
    workers = [
        Process(
            target=worker_process,
            args=(i + 1, task_queue, result_queue),
            name=f"Worker-{i + 1}"
        )
        for i in range(num_workers)
    ]
    for worker in workers:
        worker.start()

    # Start sender process
    p_sender = Process(
        target=sender_process,
        args=(result_queue, total_passed, total_received, start_time),
        name="Sender"
    )
    p_sender.start()

    # Wait for completion
    p_receiver.join()
    for worker in workers:
        worker.join()

    result_queue.put("STOP")
    p_sender.join()

    elapsed = time.perf_counter() - start_time

    print(
        f"{Color.BOLD}[Main] Total time: {elapsed:.2f} seconds{Color.RESET}",
        flush=True
    )


if __name__ == "__main__":
    main()
