"""Automated evaluator for AlphaEvolve / OpenEvolve candidates (0/1 knapsack example).

Design rules (keep these when you adapt the evaluator to a new problem):

1. Correctness is judged against a trusted reference (`reference_solve`, an exact DP),
   on many seeded random instances plus edge cases. A handful of hard-coded cases
   lets evolution memorise answers instead of improving the algorithm.
2. The candidate runs in a separate Python process with a hard timeout, so an
   infinite loop or crash in one candidate cannot stall the whole run.
3. `combined_score` depends only on solution quality, so it is deterministic and
   reproducible. Runtime is measured separately (median of repeats, import time
   excluded) and reported as a feature for MAP-Elites, not mixed into the score.
"""

import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

SEED = 12345          # fixed so every candidate sees the same instances
N_INSTANCES = 40      # random instances (plus edge cases below)
REPEATS = 3           # timing repeats per instance; the median is used
TIMEOUT_S = 20        # wall-clock limit for one candidate, all instances together

# Runs inside the child process: imports the candidate, solves every case, times solve() only.
_RUNNER = r"""
import contextlib, importlib.util, json, statistics, sys, time
path, repeats = sys.argv[1], int(sys.argv[2])
cases = json.load(sys.stdin)
real_stdout = sys.stdout
answers, total = [], 0.0
with contextlib.redirect_stdout(sys.stderr):   # candidate prints must not corrupt the result
    spec = importlib.util.spec_from_file_location("candidate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for items, cap in cases:
        items = [tuple(x) for x in items]
        times = []
        for _ in range(repeats):
            t = time.perf_counter()
            res = mod.solve(list(items), cap)   # fresh copy: candidates may mutate input
            times.append(time.perf_counter() - t)
        answers.append([int(i) for i in res])
        total += statistics.median(times)
json.dump({"answers": answers, "solve_ms": total * 1000.0}, real_stdout)
"""


def make_instances(seed: int = SEED, n: int = N_INSTANCES) -> list[tuple[list[tuple[int, int]], int]]:
    rng = random.Random(seed)
    cases = []
    for _ in range(n):
        k = rng.randint(5, 40)
        items = [(rng.randint(1, 100), rng.randint(1, 50)) for _ in range(k)]
        capacity = rng.randint(10, max(10, sum(w for _, w in items) // 2))
        cases.append((items, capacity))
    cases += [
        ([], 10),                    # no items
        ([(5, 20)], 10),             # nothing fits
        ([(5, 0), (3, 4)], 4),       # zero-weight item
        ([(7, 3)], 0),               # zero capacity
        ([(10, 5), (10, 5)], 5),     # ties
    ]
    return cases


def reference_solve(items: list[tuple[int, int]], capacity: int) -> int:
    """Exact optimum value by dynamic programming, O(n * capacity)."""
    best = [0] * (capacity + 1)
    for value, weight in items:
        for c in range(capacity, weight - 1, -1):
            best[c] = max(best[c], best[c - weight] + value)
    return best[capacity]


def _fail(error: str) -> dict[str, Any]:
    return {"combined_score": 0.0, "valid": 0.0, "error": error}


def evaluate(program_path: str) -> dict[str, Any]:
    """Evaluates a candidate program and returns metrics including combined_score (higher is better)."""
    cases = make_instances()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _RUNNER, str(program_path), str(REPEATS)],
            input=json.dumps(cases),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return _fail(f"timeout: candidate took longer than {TIMEOUT_S}s")
    if proc.returncode != 0:
        return _fail("candidate crashed: " + proc.stderr.strip()[-800:])
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return _fail("invalid runner output: " + proc.stdout[:200])

    ratios, n_optimal = [], 0
    for (items, capacity), chosen in zip(cases, out["answers"]):
        if len(set(chosen)) != len(chosen) or any(i < 0 or i >= len(items) for i in chosen):
            return _fail(f"invalid indices {chosen[:10]} for {len(items)} items")
        weight = sum(items[i][1] for i in chosen)
        if weight > capacity:
            return _fail(f"constraint violated: weight={weight} > capacity={capacity}")
        value = sum(items[i][0] for i in chosen)
        optimum = reference_solve(items, capacity)
        ratios.append(1.0 if optimum == 0 else value / optimum)
        n_optimal += value == optimum

    code = Path(program_path).read_text(encoding="utf-8")
    return {
        "combined_score": round(sum(ratios) / len(ratios), 6),
        "valid": 1.0,
        "optimality_ratio": round(sum(ratios) / len(ratios), 6),
        "optimal_fraction": round(n_optimal / len(cases), 4),
        "runtime_ms": round(out["solve_ms"], 3),
        "complexity": len(code),
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "initial_program.py"
    print(json.dumps(evaluate(target), indent=2))
