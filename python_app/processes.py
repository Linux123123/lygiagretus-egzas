"""
Process definitions for Python Worker Application.
Author: IFF-3-2 Aleksandravicius Linas

Processes communicate via multiprocessing.Queue.
Network communication with C++ uses ZeroMQ (binary protocol).
"""

import struct
import time
from multiprocessing import Queue
from typing import Any, Tuple

import zmq

from colors import Color
from config import ZMQ_PULL_ADDR, ZMQ_PUSH_ADDR
from functions import compute_stability_score, passes_stability_filter

# Type aliases
ServerTask = Tuple[int, float, int]  # (id, load, uptime)
ServerResult = Tuple[int, float]     # (id, stability)


def worker_process(
    worker_id: int,
    input_queue: "Queue[Any]",
    output_queue: "Queue[Any]"
) -> None:
    """
    Worker process: computes stability score and applies Filter 2.

    Only records with stability >= 50.0 are sent to output queue.
    """
    processed = 0
    accepted = 0

    while True:
        try:
            item = input_queue.get()

            if item == "STOP":
                break

            server_id, load, uptime = item
            stability = compute_stability_score(server_id, load, uptime)
            processed += 1

            if passes_stability_filter(stability):
                output_queue.put((server_id, stability))
                accepted += 1

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(
                f"{Color.RED}[Worker {worker_id}] Error: {e}{Color.RESET}",
                flush=True
            )

    print(
        f"{Color.CYAN}[Worker {worker_id}]{Color.RESET} "
        f"Done: {accepted}/{processed} passed",
        flush=True
    )


def receiver_process(
    task_queue: "Queue[Any]",
    num_workers: int,
    total_received: Any = None
) -> None:
    """
    Receiver process: gets data from C++ via ZMQ.

    Binary format: id(4) + load(4) + uptime(4) = 12 bytes per record.
    """
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind(ZMQ_PULL_ADDR)

    received = 0

    try:
        while True:
            msg = socket.recv()

            # Stop signal: single byte 0xFF
            if len(msg) == 1 and msg[0] == 0xFF:
                break

            # Binary format: id(4) + load(4) + uptime(4)
            server_id, load, uptime = struct.unpack("ifi", msg)
            task_queue.put((server_id, load, uptime))
            received += 1

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"{Color.RED}[Receiver] Error: {e}{Color.RESET}", flush=True)

    finally:
        if total_received is not None:
            total_received.value = received
        # Signal all workers to stop
        for _ in range(num_workers):
            task_queue.put("STOP")
        socket.close()
        context.term()

    print(
        f"{Color.GREEN}[Receiver]{Color.RESET} "
        f"Received {received} records from C++",
        flush=True
    )


def sender_process(
    result_queue: "Queue[Any]",
    total_passed: Any = None,
    total_received: Any = None,
    start_time: float = 0.0
) -> None:
    """
    Sender process: sends filtered results back to C++ via ZMQ.

    Binary format: id(4) + stability(4) = 8 bytes per result.
    """
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)

    # Retry connection with timeout
    for _ in range(30):
        try:
            socket.connect(ZMQ_PUSH_ADDR)
            break
        except zmq.ZMQError:
            time.sleep(1.0)

    sent = 0

    try:
        while True:
            item = result_queue.get()

            if item == "STOP":
                socket.send(bytes([0xFF]))  # Stop signal
                break

            server_id, stability = item
            msg = struct.pack("if", server_id, stability)
            socket.send(msg)
            sent += 1

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"{Color.RED}[Sender] Error: {e}{Color.RESET}", flush=True)

    finally:
        if total_passed is not None:
            total_passed.value = sent

        socket.close()
        context.term()

    print(
        f"{Color.MAGENTA}[Sender]{Color.RESET} Sent {sent} results to C++",
        flush=True
    )

    if total_received is not None and start_time > 0:
        elapsed = time.perf_counter() - start_time
        elapsed_ms = int(elapsed * 1000)
        print(
            f"{Color.BLUE}[Main]{Color.RESET} "
            f"{sent}/{total_received.value} passed, {elapsed_ms} ms",
            flush=True
        )
