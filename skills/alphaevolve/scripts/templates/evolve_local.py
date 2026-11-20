#!/usr/bin/env python3
"""Local archive & evaluation CLI for agent-driven AlphaEvolve loops (Mode A).

Commands:
  init      evaluate initial_program.py and start archive.json
  sample    show parents to mutate next: top scorers + diverse picks
  evaluate  register a candidate file, score it, update best_program.py
  status    best candidate and recent history

One loop iteration in Mode A:
  1. `sample` to pick a parent program.
  2. The agent writes a mutated copy of that parent.
  3. `evaluate --candidate new.py --parent-id gen_XXX --rationale "..."` to score it.
  Repeat. The archive remembers every attempt; best_program.py always holds the winner.

Workspace files:
  archive.json         every generation with its parent, rationale and metrics
  candidates/gen_*.py  a frozen copy of each evaluated program
  best_program.py      copy of the highest scoring valid candidate
"""

import argparse
import importlib.util
import json
import random
import shutil
import sys
import time
from pathlib import Path


def load_evaluator(workspace: Path):
    """Imports the workspace's evaluator.py, so each workspace can have its own evaluator."""
    spec = importlib.util.spec_from_file_location("evaluator", str(workspace / "evaluator.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_archive(workspace: Path) -> dict:
    path = workspace / "archive.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"generations": []}


def save_archive(workspace: Path, data: dict) -> None:
    (workspace / "archive.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _score(g: dict) -> float:
    # A generation without a score sorts last instead of raising an error.
    return g["metrics"].get("combined_score", float("-inf"))


def _valid(g: dict) -> bool:
    # Evaluators that do not report "valid" are treated as valid.
    return bool(g["metrics"].get("valid", 1.0))


def _entry(workspace: Path, gen_id: str, parent_id, path: Path, rationale: str, metrics: dict) -> dict:
    """One archive record. parent_id links generations into a family tree."""
    return {
        "id": gen_id,
        "parent_id": parent_id,
        "path": path.relative_to(workspace).as_posix(),   # relative, so the workspace can be moved
        "rationale": rationale,
        "metrics": metrics,
        "code_length": len(path.read_text(encoding="utf-8")),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _update_best(workspace: Path, archive: dict) -> None:
    """Points best_id at the top valid generation and copies it to best_program.py."""
    valid = [g for g in archive["generations"] if _valid(g)]
    if valid:
        # Ties on score go to the earlier (usually simpler) program.
        # max() keeps the first maximum it sees, and generations are stored in order.
        best = max(valid, key=_score)
        archive["best_id"] = best["id"]
        shutil.copyfile(workspace / best["path"], workspace / "best_program.py")


def cmd_init(workspace: Path) -> None:
    """Starts a fresh archive with initial_program.py as gen_000. Overwrites any old archive."""
    candidates = workspace / "candidates"
    candidates.mkdir(parents=True, exist_ok=True)
    gen0 = candidates / "gen_000.py"
    shutil.copyfile(workspace / "initial_program.py", gen0)
    metrics = load_evaluator(workspace).evaluate(str(gen0))
    archive = {"generations": [_entry(workspace, "gen_000", None, gen0, "Initial baseline program", metrics)]}
    _update_best(workspace, archive)
    save_archive(workspace, archive)
    print(json.dumps(archive["generations"][0], indent=2, ensure_ascii=False))


def cmd_sample(workspace: Path, k: int, seed: int | None) -> None:
    """Exploit (top-k by score) + explore (random valid picks from other complexity buckets)."""
    gens = [g for g in load_archive(workspace)["generations"] if _valid(g)]
    if not gens:
        raise SystemExit("archive is empty or has no valid candidates; run init first")

    # Exploit: the k best programs. Mutating these refines what already works.
    top = sorted(gens, key=_score, reverse=True)[:k]
    rest = [g for g in gens if g not in top]

    # Explore: up to 2 programs from different size buckets. Mutating only the top
    # programs makes the population converge on one idea; these keep other ideas alive.
    # This is a lightweight stand-in for OpenEvolve's MAP-Elites grid.
    rng = random.Random(seed)
    explore = []
    if rest:
        by_bucket: dict[int, list] = {}
        for g in rest:
            # Bucket by code length in steps of 500 characters (0-499, 500-999, ...).
            by_bucket.setdefault(g["code_length"] // 500, []).append(g)
        for bucket in rng.sample(sorted(by_bucket), min(2, len(by_bucket))):
            explore.append(rng.choice(by_bucket[bucket]))

    fmt = lambda g, role: {"role": role, "id": g["id"], "score": _score(g), "path": g["path"],
                           "rationale": g["rationale"], "metrics": g["metrics"]}
    print(json.dumps([fmt(g, "exploit") for g in top] + [fmt(g, "explore") for g in explore],
                     indent=2, ensure_ascii=False))


def cmd_evaluate(workspace: Path, candidate: Path, parent_id: str, rationale: str) -> None:
    """Scores one candidate, stores it as the next generation and reports the change vs its parent."""
    archive = load_archive(workspace)
    if not archive["generations"]:
        raise SystemExit("run init first")
    # Generation ids are sequential: gen_000, gen_001, ...
    gen_id = f"gen_{len(archive['generations']):03d}"
    stored = workspace / "candidates" / f"{gen_id}.py"
    stored.parent.mkdir(parents=True, exist_ok=True)
    # Copy first, then evaluate the copy. Later edits to the original file
    # cannot change what was scored.
    if candidate.resolve() != stored.resolve():
        shutil.copyfile(candidate, stored)
    metrics = load_evaluator(workspace).evaluate(str(stored))
    entry = _entry(workspace, gen_id, parent_id, stored, rationale, metrics)
    archive["generations"].append(entry)
    parent = next((g for g in archive["generations"] if g["id"] == parent_id), None)
    _update_best(workspace, archive)
    save_archive(workspace, archive)
    # Positive delta: the mutation helped. Negative: it hurt. None: unknown parent id.
    delta = None if parent is None else round(_score(entry) - _score(parent), 6)
    print(json.dumps({"evaluated": entry, "delta_vs_parent": delta, "best_id": archive.get("best_id")},
                     indent=2, ensure_ascii=False))


def cmd_status(workspace: Path, held_out: bool = False) -> None:
    """Prints the best generation and a one-line history of every generation."""
    archive = load_archive(workspace)
    if not archive["generations"]:
        # No archive yet: still useful to see how the baseline scores.
        metrics = load_evaluator(workspace).evaluate(str(workspace / "initial_program.py"))
        print(json.dumps({"status": "uninitialized", "baseline_metrics": metrics}, indent=2))
        return
    best = next((g for g in archive["generations"] if g["id"] == archive.get("best_id")), None)
    table = [{"id": g["id"], "parent": g["parent_id"], "score": _score(g), "rationale": g["rationale"]}
             for g in archive["generations"]]
    result: dict = {"total_generations": len(table), "best_candidate": best, "history": table}
    if held_out and best is not None:
        evaluator = load_evaluator(workspace)
        try:
            result["held_out_metrics"] = evaluator.evaluate(str(workspace / best["path"]), held_out=True)
        except TypeError:
            result["held_out_metrics"] = {"error": "evaluator.evaluate() does not accept held_out=True"}
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    # Windows consoles default to a legacy code page; force UTF-8 so non-ASCII rationales print.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Local AlphaEvolve runner")
    p.add_argument("action", choices=["init", "sample", "evaluate", "status"])
    p.add_argument("--workspace", default=".", help="path to the evolve workspace")
    p.add_argument("--candidate", help="candidate .py file (evaluate)")
    p.add_argument("--parent-id", default="gen_000", help="parent generation id (evaluate)")
    p.add_argument("--rationale", default="", help="what the mutation changed and why (evaluate)")
    p.add_argument("-k", type=int, default=3, help="number of top parents (sample)")
    p.add_argument("--seed", type=int, default=None, help="seed for explore picks (sample)")
    p.add_argument("--held-out", action="store_true", help="also score best_program.py on held-out data (status)")
    a = p.parse_args()

    ws = Path(a.workspace).resolve()
    if a.action == "init":
        cmd_init(ws)
    elif a.action == "sample":
        cmd_sample(ws, a.k, a.seed)
    elif a.action == "evaluate":
        if not a.candidate:
            raise SystemExit("--candidate is required for evaluate")
        cmd_evaluate(ws, Path(a.candidate), a.parent_id, a.rationale)
    else:
        cmd_status(ws, held_out=a.held_out)


if __name__ == "__main__":
    main()
