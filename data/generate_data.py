#!/usr/bin/env python3
"""
Data Generator using PyOpenCL for exact reliability computation.
Author: IFF-3-2 Aleksandravicius Linas

Uses the same OpenCL kernel as the C++ application for identical results.
"""

import json
import math
import random
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Tuple

import numpy as np
import pyopencl as cl


# Constants matching C++ and Python apps
RELIABILITY_ITERATIONS = 4_000_000
STABILITY_ITERATIONS = 600_000
THRESHOLD = 50.0
MARGIN = 2.0  # Safety margin for threshold edge cases

LOCATIONS = [
    "Vilnius", "Kaunas", "Klaipeda", "Siauliai", "Panevezys",
    "Alytus", "Marijampole", "Mazeikiai", "Jonava", "Utena",
    "Kedainiai", "Telsiai", "Visaginas", "Taurage", "Ukmerge"
]


class DatasetType(IntEnum):
    BOTH_PASS = 1      # rel >= 50, stab >= 50
    REL_FAIL = 2       # rel < 50, stab >= 50
    STAB_FAIL = 3      # rel >= 50, stab < 50
    RANDOM = 4         # Mixed


@dataclass
class ServerRecord:
    id: int
    location: str
    uptime: int
    load: float
    reliability: float = 0.0
    stability: float = 0.0


# OpenCL kernel source - identical to C++ app's kernels.cl
OPENCL_KERNEL_SOURCE = """
#define RELIABILITY_ITERATIONS 4000000

__kernel void compute_reliability(
    __global const int* input_uptimes,
    __global const float* input_loads,
    __global float* output_reliability,
    const int count
) {
    int gid = get_global_id(0);

    if (gid < count) {
        int uptime = input_uptimes[gid];
        float load = input_loads[gid];

        float reliability = 0.5f;

        for (int i = 0; i < RELIABILITY_ITERATIONS; i++) {
            float factor1 = sin((float)uptime / 1000.0f * (float)i);
            float factor2 = cos(load * (float)i);
            reliability = fabs(sin(reliability + factor1 - factor2));
        }

        output_reliability[gid] = reliability * 100.0f;
    }
}
"""


class OpenCLReliabilityComputer:
    """Computes reliability using OpenCL - identical to C++ application."""

    def __init__(self) -> None:
        self.device = self._select_device()
        self.ctx = cl.Context([self.device])
        self.queue = cl.CommandQueue(self.ctx)
        self.program = cl.Program(self.ctx, OPENCL_KERNEL_SOURCE).build()

    def _select_device(self) -> cl.Device:
        platforms = cl.get_platforms()

        # Try GPU first
        for plat in platforms:
            try:
                devices = plat.get_devices(device_type=cl.device_type.GPU)
                if devices:
                    print(f"[OpenCL] Platform: {plat.name}")
                    print(f"[OpenCL] Device: {devices[0].name}")
                    return devices[0]
            except cl.RuntimeError:
                continue

        # Fall back to CPU
        for plat in platforms:
            try:
                devices = plat.get_devices(device_type=cl.device_type.CPU)
                if devices:
                    print(f"[OpenCL] Platform: {plat.name}")
                    print(f"[OpenCL] Device: {devices[0].name}")
                    return devices[0]
            except cl.RuntimeError:
                continue

        raise RuntimeError("No OpenCL device found!")

    def compute_batch(self, records: List[Dict]) -> List[float]:
        if not records:
            return []

        count = len(records)
        uptimes = np.array([r["uptime"] for r in records], dtype=np.int32)
        loads = np.array([r["load"] for r in records], dtype=np.float32)
        results = np.zeros(count, dtype=np.float32)

        mf = cl.mem_flags
        uptimes_buf = cl.Buffer(
            self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=uptimes
        )
        loads_buf = cl.Buffer(
            self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=loads
        )
        results_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, results.nbytes)

        self.program.compute_reliability(
            self.queue, (count,), None,
            uptimes_buf, loads_buf, results_buf, np.int32(count)
        )

        cl.enqueue_copy(self.queue, results, results_buf)
        self.queue.finish()

        return results.tolist()


def compute_stability(uptime: int, load: float) -> float:
    stability = 0.5
    load_factor = load * 0.001
    uptime_factor = uptime / 10000.0

    for i in range(STABILITY_ITERATIONS):
        factor1 = math.cos(load_factor * i)
        factor2 = math.sin(uptime_factor * i)
        factor3 = math.tan(stability * 0.01) if abs(stability) < 100 else 0.0
        stability = abs(math.sin(stability + factor1 * factor2 - factor3 * 0.001))

    return stability * 100.0


def generate_random_params() -> Tuple[int, float]:
    uptime = random.randint(100, 9999)
    load = round(random.uniform(10.0, 90.0), 2)
    return uptime, load


def generate_candidate_records(count: int) -> List[Dict]:
    return [
        {
            "id": i + 1,
            "location": random.choice(LOCATIONS),
            "uptime": (params := generate_random_params())[0],
            "load": params[1]
        }
        for i in range(count)
    ]


def should_accept_record(
    reliability: float,
    stability: float,
    condition: DatasetType
) -> bool:
    rel_pass = reliability >= (THRESHOLD + MARGIN)
    rel_fail = reliability <= (THRESHOLD - MARGIN)
    stab_pass = stability >= (THRESHOLD + MARGIN)
    stab_fail = stability <= (THRESHOLD - MARGIN)

    if condition == DatasetType.BOTH_PASS:
        return rel_pass and stab_pass
    elif condition == DatasetType.REL_FAIL:
        return rel_fail and stab_pass
    elif condition == DatasetType.STAB_FAIL:
        return rel_pass and stab_fail
    else:  # RANDOM
        return True


def generate_dataset(
    filename: str,
    num_records: int,
    condition: DatasetType,
    opencl: OpenCLReliabilityComputer
) -> None:
    print(f"\nGenerating {filename} with {num_records} records "
          f"(Condition {condition.name})...")

    all_records: List[Dict] = []
    batch_size = 100
    max_attempts = num_records * 50

    attempts = 0
    while len(all_records) < num_records and attempts < max_attempts:
        needed = min(batch_size, (num_records - len(all_records)) * 3)
        candidates = generate_candidate_records(needed)

        # Compute reliability using OpenCL
        reliabilities = opencl.compute_batch(candidates)

        for idx, record in enumerate(candidates):
            if len(all_records) >= num_records:
                break

            reliability = reliabilities[idx]
            stability = compute_stability(record["uptime"], record["load"])

            if should_accept_record(reliability, stability, condition):
                record["rel"] = reliability
                record["stab"] = stability
                record["id"] = len(all_records) + 1
                all_records.append(record)

        attempts += needed
        print(f"  Progress: {len(all_records)}/{num_records} records found...",
              end="\r")

    print(f"  Progress: {len(all_records)}/{num_records} records found.    ")

    if len(all_records) < num_records:
        print(f"  WARNING: Only found {len(all_records)} matching records!")

    # Calculate statistics
    stats = {
        "total": len(all_records),
        "pass_both": 0,
        "pass_rel": 0,
        "pass_stab": 0,
        "fail_both": 0
    }

    for record in all_records:
        rel_pass = record["rel"] >= THRESHOLD
        stab_pass = record["stab"] >= THRESHOLD

        if rel_pass and stab_pass:
            stats["pass_both"] += 1
        elif rel_pass:
            stats["pass_rel"] += 1
        elif stab_pass:
            stats["pass_stab"] += 1
        else:
            stats["fail_both"] += 1

    # Prepare JSON output (without computed values)
    json_servers = [
        {
            "id": r["id"],
            "location": r["location"],
            "uptime": r["uptime"],
            "load": r["load"]
        }
        for r in all_records
    ]

    with open(filename, "w") as f:
        json.dump({"servers": json_servers}, f, indent=2)

    print(f"  Saved {filename}")
    print(f"  Stats: {stats}")


def main() -> None:
    print("=" * 60)
    print("Data Generator with PyOpenCL")
    print(f"Reliability iterations: {RELIABILITY_ITERATIONS:,}")
    print(f"Stability iterations: {STABILITY_ITERATIONS:,}")
    print("=" * 60)

    opencl = OpenCLReliabilityComputer()

    datasets = [
        ("IFF-3-2_AleksandraviciusLinas_L2_dat_1.json", 300, DatasetType.BOTH_PASS),
        ("IFF-3-2_AleksandraviciusLinas_L2_dat_2.json", 300, DatasetType.REL_FAIL),
        ("IFF-3-2_AleksandraviciusLinas_L2_dat_3.json", 300, DatasetType.STAB_FAIL),
        ("IFF-3-2_AleksandraviciusLinas_L2_dat_4.json", 300, DatasetType.RANDOM),
    ]

    for filename, count, condition in datasets:
        generate_dataset(filename, count, condition, opencl)

    print("\n" + "=" * 60)
    print("All datasets generated!")
    print("=" * 60)


if __name__ == "__main__":
    main()
