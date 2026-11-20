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

Flow of one evaluation:
    make_instances() -> run candidate in child process (_RUNNER) -> check every answer
    against the constraints -> compare its value with reference_solve() -> build metrics.
"""

import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

# Knobs to tune when you adapt this file. Changing SEED or N_INSTANCES changes every
# score, so do not change them in the middle of a run or old scores stop being comparable.
SEED = 12345          # fixed so every candidate sees the same evolution instances
HELD_OUT_SEED = 67890 # untouched seed for final held-out check (--held-out)
N_INSTANCES = 40      # random instances (plus edge cases below)
REPEATS = 3           # timing repeats per instance; the median is used
TIMEOUT_S = 20        # wall-clock limit for one candidate, all instances together
MAX_CODE_CHARS = 8000 # guards against embedding a lookup table of per-item answers

# Runs inside the child process: imports the candidate, solves every case, times solve() only.
# It is a string because it is passed to `python -c`. The parent sends the test cases on
# stdin as JSON and reads the answers back from stdout as JSON.
# Tip for corpus / CSV / TSV tasks: instead of piping a large dataset through stdin,
# load the dataset file read-only inside _RUNNER (or pass its path via sys.argv).
_RUNNER = r"""
import contextlib, importlib.util, json, statistics, sys, time
path, repeats = sys.argv[1], int(sys.argv[2])
cases = json.load(sys.stdin)
# Keep a handle on the real stdout before redirecting, so only our JSON goes there.
real_stdout = sys.stdout
answers, total = [], 0.0
with contextlib.redirect_stdout(sys.stderr):   # candidate prints must not corrupt the result
    # Import the candidate file as a module. Import time is not part of the timing below.
    spec = importlib.util.spec_from_file_location("candidate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for items, cap in cases:
        items = [tuple(x) for x in items]       # JSON turns tuples into lists; restore them
        times = []
        for _ in range(repeats):
            t = time.perf_counter()
            res = mod.solve(list(items), cap)   # fresh copy: candidates may mutate input
            times.append(time.perf_counter() - t)
        # Only the last answer is kept; repeats exist for timing, not for scoring.
        answers.append([int(i) for i in res])
        # Median is robust to one slow repeat (GC pause, OS scheduling).
        total += statistics.median(times)
json.dump({"answers": answers, "solve_ms": total * 1000.0}, real_stdout)
"""


def make_instances(seed: int = SEED, n: int = N_INSTANCES) -> list[tuple[list[tuple[int, int]], int]]:
    """Builds the test set: n seeded random instances followed by fixed edge cases."""
    # A private Random object, so the global random state cannot change the instances.
    rng = random.Random(seed)
    cases = []
    for _ in range(n):
        k = rng.randint(5, 40)                                   # number of items
        items = [(rng.randint(1, 100), rng.randint(1, 50)) for _ in range(k)]  # (value, weight)
        # Capacity up to half the total weight, so the problem is never trivial
        # (taking everything would never fit) but still has room to choose.
        capacity = rng.randint(10, max(10, sum(w for _, w in items) // 2))
        cases.append((items, capacity))
    # Edge cases catch candidates that only work on "normal" inputs.
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
    # best[c] = highest value reachable with total weight at most c, using the items seen so far.
    best = [0] * (capacity + 1)
    for value, weight in items:
        # Walk c downwards so each item is used at most once (the 0/1 rule).
        # Walking upwards would let the same item be added again (unbounded knapsack).
        for c in range(capacity, weight - 1, -1):
            best[c] = max(best[c], best[c - weight] + value)
    return best[capacity]


def _fail(error: str) -> dict[str, Any]:
    """Metrics for a rejected candidate. Score 0 keeps it out of best_program.py."""
    return {"combined_score": 0.0, "valid": 0.0, "error": error}


def evaluate(program_path: str, held_out: bool = False) -> dict[str, Any]:
    """Evaluates a candidate program and returns metrics including combined_score (higher is better).

    Args:
        program_path: Path to the candidate .py file.
        held_out: If True, evaluates on HELD_OUT_SEED (unseen during evolution) to check generalisation.
    """
    code = Path(program_path).read_text(encoding="utf-8")
    if len(code) > MAX_CODE_CHARS:
        return _fail(f"code too long ({len(code)} chars > {MAX_CODE_CHARS}): rules must stay general, not memorise items")

    cases = make_instances(seed=HELD_OUT_SEED if held_out else SEED)

    # Step 1: run the candidate in its own process with a hard time limit.
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
        # Keep only the tail of stderr: the traceback's last lines say what went wrong.
        return _fail("candidate crashed: " + proc.stderr.strip()[-800:])
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return _fail("invalid runner output: " + proc.stdout[:200])

    # Step 2: check every answer. One invalid answer rejects the whole candidate,
    # so evolution cannot trade correctness for a higher average.
    ratios, n_optimal = [], 0
    for (items, capacity), chosen in zip(cases, out["answers"]):
        # Each index must be in range and used at most once.
        if len(set(chosen)) != len(chosen) or any(i < 0 or i >= len(items) for i in chosen):
            return _fail(f"invalid indices {chosen[:10]} for {len(items)} items")
        weight = sum(items[i][1] for i in chosen)
        if weight > capacity:
            return _fail(f"constraint violated: weight={weight} > capacity={capacity}")
        # Step 3: score quality as value / optimum, so 1.0 means optimal on that instance.
        value = sum(items[i][0] for i in chosen)
        optimum = reference_solve(items, capacity)
        ratios.append(1.0 if optimum == 0 else value / optimum)   # optimum 0: any valid answer is optimal
        n_optimal += value == optimum

    # Step 4: build the metrics. Only combined_score decides the best program.
    # runtime_ms and complexity are features for MAP-Elites (diversity), not part of the score.
    return {
        "combined_score": round(sum(ratios) / len(ratios), 6),
        "valid": 1.0,
        "split": "held_out" if held_out else "evolve",
        "optimality_ratio": round(sum(ratios) / len(ratios), 6),
        "optimal_fraction": round(n_optimal / len(cases), 4),
        "runtime_ms": round(out["solve_ms"], 3),
        "complexity": len(code),   # code length in characters, a rough size measure
    }


if __name__ == "__main__":
    # Manual check: python evaluator.py [some_candidate.py] [--held-out]
    args = [a for a in sys.argv[1:] if a != "--held-out"]
    use_held_out = "--held-out" in sys.argv[1:]
    target = args[0] if args else "initial_program.py"
    print(json.dumps(evaluate(target, held_out=use_held_out), indent=2))
