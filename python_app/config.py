"""
Configuration constants.
Author: IFF-3-2 Aleksandravicius Linas
"""

import multiprocessing

# ZeroMQ addresses
ZMQ_PULL_ADDR = "tcp://127.0.0.1:5557"
ZMQ_PUSH_ADDR = "tcp://127.0.0.1:5558"

# Computation parameters
STABILITY_ITERATIONS = 600_000
STABILITY_THRESHOLD = 50.0


def get_worker_count(use_half_cpu: bool = False) -> int:
    """Determine optimal number of worker processes."""
    cpu_count = multiprocessing.cpu_count()
    if use_half_cpu:
        return max(1, cpu_count // 2)
    return max(1, cpu_count - 1)
