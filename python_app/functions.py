"""
Stability score calculation (Filter 2).
Author: IFF-3-2 Aleksandravicius Linas
"""

import math

from config import STABILITY_ITERATIONS, STABILITY_THRESHOLD


def compute_stability_score(server_id: int, load: float, uptime: int) -> float:
    """Compute stability score using iterative trigonometric calculations."""
    stability = 0.5 + (server_id % 10) * 0.01

    for i in range(STABILITY_ITERATIONS):
        factor1 = math.cos(load * 0.001 * i)
        factor2 = math.sin(uptime / 10000.0 * i)
        factor3 = (
            math.tan(stability * 0.01) if abs(stability) < 100 else 0.0
        )
        stability = abs(
            math.sin(stability + factor1 * factor2 - factor3 * 0.001)
        )

    return stability * 100.0


def passes_stability_filter(stability: float) -> bool:
    """Check if stability passes Filter 2."""
    return stability >= STABILITY_THRESHOLD
