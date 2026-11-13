#!/usr/bin/env python3
"""Scaffolds an AlphaEvolve / OpenEvolve optimization workspace and local archive manager."""

import argparse
import json
import os
from pathlib import Path
import shutil
import textwrap

INITIAL_PROGRAM_TEMPLATE = """\
\"\"\"Baseline candidate program for AlphaEvolve optimization.\"\"\"

# EVOLVE-BLOCK-START
def solve(items: list[tuple[int, int]], capacity: int) -> list[int]:
    \"\"\"Solves 0/1 knapsack heuristically.
    Args:
        items: List of (value, weight) tuples.
        capacity: Maximum allowed weight.
    Returns:
        List of selected item indices.
    \"\"\"
    indexed = sorted(
        enumerate(items),
        key=lambda x: x[1][0] / max(x[1][1], 1e-9),
        reverse=True,
    )
    selected = []
    total_weight = 0
    for idx, (val, weight) in indexed:
        if total_weight + weight <= capacity:
            selected.append(idx)
            total_weight += weight
    return selected
# EVOLVE-BLOCK-END
"""

EVALUATOR_TEMPLATE = """\
\"\"\"Automated evaluator for AlphaEvolve / OpenEvolve candidates.\"\"\"

import importlib.util
import time
from typing import Any


def _load_module(program_path: str):
    spec = importlib.util.spec_from_file_location("candidate_module", program_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load candidate from {program_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate(program_path: str) -> dict[str, Any]:
    \"\"\"Evaluates a candidate program and returns metrics including combined_score.\"\"\"
    start = time.perf_counter()
    try:
        mod = _load_module(program_path)
        test_cases = [
            ([(60, 10), (100, 20), (120, 30)], 50, 220),
            ([(10, 5), (40, 4), (30, 6), (50, 3)], 10, 90),
            ([(24, 24), (13, 10), (23, 10), (15, 7), (16, 7)], 26, 51),
        ]
        ratios = []
        for items, capacity, optimal in test_cases:
            chosen = mod.solve(items, capacity)
            total_w = sum(items[i][1] for i in chosen)
            total_v = sum(items[i][0] for i in chosen)
            if total_w > capacity or len(set(chosen)) != len(chosen):
                return {
                    "combined_score": 0.0,
                    "valid": False,
                    "error": f"Constraint violated: weight={total_w}, capacity={capacity}",
                }
            ratios.append(total_v / optimal)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        mean_ratio = sum(ratios) / len(ratios)
        speed_bonus = max(0.0, 1.0 - (elapsed_ms / 1000.0)) * 0.01
        return {
            "combined_score": round(mean_ratio + speed_bonus, 6),
            "optimality_ratio": round(mean_ratio, 6),
            "runtime_ms": round(elapsed_ms, 3),
            "valid": True,
        }
    except Exception as exc:
        return {
            "combined_score": 0.0,
            "valid": False,
            "error": str(exc),
        }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "initial_program.py"
    print(json.dumps(evaluate(target), indent=2) if "json" in globals() else evaluate(target))
"""

CONFIG_YAML_TEMPLATE = """\
# OpenEvolve / AlphaEvolve configuration
max_iterations: 50
checkpoint_interval: 10
log_level: INFO

llm:
  primary_model: "gemini-2.5-flash"
  secondary_model: "gemini-2.5-pro"
  temperature: 0.7

database:
  population_size: 40
  num_islands: 4
  feature_dimensions:
    - "complexity"
    - "runtime_ms"

evaluator:
  timeout: 30
  cascade_evaluation: true
"""

EVOLVE_LOCAL_TEMPLATE = """\
#!/usr/bin/env python3
\"\"\"Local archive & evaluation CLI for Native Agent-Driven AlphaEvolve loops.\"\"\"

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import time


def load_evaluator(workspace: Path):
    eval_path = workspace / "evaluator.py"
    spec = importlib.util.spec_from_file_location("evaluator", str(eval_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_archive(workspace: Path) -> dict:
    archive_path = workspace / "archive.json"
    if archive_path.exists():
        return json.loads(archive_path.read_text(encoding="utf-8"))
    return {"generations": []}


def save_archive(workspace: Path, data: dict):
    archive_path = workspace / "archive.json"
    archive_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_init(workspace: Path):
    candidates_dir = workspace / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    initial = workspace / "initial_program.py"
    gen0 = candidates_dir / "gen_000.py"
    shutil.copyfile(initial, gen0)
    evaluator = load_evaluator(workspace)
    metrics = evaluator.evaluate(str(gen0))
    entry = {
        "id": "gen_000",
        "parent_id": None,
        "path": str(gen0.relative_to(workspace)),
        "rationale": "Initial baseline program",
        "metrics": metrics,
        "code_length": len(gen0.read_text(encoding="utf-8")),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    archive = {"generations": [entry], "best_id": "gen_000"}
    save_archive(workspace, archive)
    shutil.copyfile(gen0, workspace / "best_program.py")
    print(json.dumps(entry, indent=2, ensure_ascii=False))


def cmd_evaluate(workspace: Path, candidate: Path, parent_id: str, rationale: str):
    archive = load_archive(workspace)
    next_idx = len(archive["generations"])
    gen_id = f"gen_{next_idx:03d}"
    candidates_dir = workspace / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    stored_path = candidates_dir / f"{gen_id}.py"
    if candidate.resolve() != stored_path.resolve():
        shutil.copyfile(candidate, stored_path)

    evaluator = load_evaluator(workspace)
    metrics = evaluator.evaluate(str(stored_path))
    entry = {
        "id": gen_id,
        "parent_id": parent_id,
        "path": str(stored_path.relative_to(workspace)),
        "rationale": rationale,
        "metrics": metrics,
        "code_length": len(stored_path.read_text(encoding="utf-8")),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    archive["generations"].append(entry)

    valid_gens = [g for g in archive["generations"] if g["metrics"].get("valid", True)]
    if valid_gens:
        best = max(valid_gens, key=lambda g: g["metrics"].get("combined_score", float("-inf")))
        archive["best_id"] = best["id"]
        shutil.copyfile(workspace / best["path"], workspace / "best_program.py")

    save_archive(workspace, archive)
    print(json.dumps({"evaluated": entry, "best_id": archive.get("best_id")}, indent=2, ensure_ascii=False))


def cmd_status(workspace: Path):
    archive = load_archive(workspace)
    if not archive["generations"]:
        evaluator = load_evaluator(workspace)
        metrics = evaluator.evaluate(str(workspace / "initial_program.py"))
        print(json.dumps({"status": "uninitialized", "baseline_metrics": metrics}, indent=2))
        return
    best_id = archive.get("best_id")
    best = next((g for g in archive["generations"] if g["id"] == best_id), None)
    print(
        json.dumps(
            {
                "total_generations": len(archive["generations"]),
                "best_candidate": best,
                "recent": archive["generations"][-5:],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Local AlphaEvolve Runner")
    parser.add_argument("action", choices=["init", "evaluate", "status"])
    parser.add_argument("--workspace", default=".", help="Path to evolve workspace")
    parser.add_argument("--candidate", help="Path to candidate python file")
    parser.add_argument("--parent-id", default="gen_000", help="Parent generation ID")
    parser.add_argument("--rationale", default="", help="Mutation rationale")
    args = parser.parse_args()

    ws = Path(args.workspace).resolve()
    if args.action == "init":
        cmd_init(ws)
    elif args.action == "evaluate":
        if not args.candidate:
            raise SystemExit("--candidate is required for evaluate")
        cmd_evaluate(ws, Path(args.candidate), args.parent_id, args.rationale)
    elif args.action == "status":
        cmd_status(ws)


if __name__ == "__main__":
    main()
"""


def scaffold(target_dir: Path, task_name: str):
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "candidates").mkdir(exist_ok=True)

    files = {
        "initial_program.py": INITIAL_PROGRAM_TEMPLATE,
        "evaluator.py": EVALUATOR_TEMPLATE,
        "config.yaml": CONFIG_YAML_TEMPLATE,
        "evolve_local.py": EVOLVE_LOCAL_TEMPLATE,
    }
    created = []
    for name, content in files.items():
        dest = target_dir / name
        if not dest.exists():
            dest.write_text(textwrap.dedent(content), encoding="utf-8")
            created.append(str(dest))
    print(json.dumps({"task": task_name, "workspace": str(target_dir.resolve()), "created_files": created}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold an AlphaEvolve workspace")
    parser.add_argument("--target-dir", default="./evolve_workspace", help="Directory to create")
    parser.add_argument("--task-name", default="optimization_task", help="Name of optimization task")
    args = parser.parse_args()
    scaffold(Path(args.target_dir), args.task_name)
