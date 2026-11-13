"""Baseline candidate program for AlphaEvolve optimization (0/1 knapsack example).

Only the code between the EVOLVE-BLOCK markers is mutated. Keep the signature of
`solve` stable: the evaluator calls `solve(items, capacity)`.
"""

# EVOLVE-BLOCK-START
def solve(items: list[tuple[int, int]], capacity: int) -> list[int]:
    """Solves 0/1 knapsack heuristically.

    Args:
        items: List of (value, weight) tuples.
        capacity: Maximum allowed total weight.
    Returns:
        Indices of the selected items (each at most once).
    """
    indexed = sorted(
        enumerate(items),
        key=lambda x: x[1][0] / max(x[1][1], 1e-9),
        reverse=True,
    )
    selected = []
    total_weight = 0
    for idx, (_value, weight) in indexed:
        if total_weight + weight <= capacity:
            selected.append(idx)
            total_weight += weight
    return selected
# EVOLVE-BLOCK-END
