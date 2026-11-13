#!/usr/bin/env python3
"""Scaffolds an AlphaEvolve / OpenEvolve optimization workspace from ./templates.

Creates initial_program.py, evaluator.py, config.yaml and evolve_local.py.
Existing files are never overwritten.
"""

import argparse
import json
import shutil
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent / "templates"
FILES = ("initial_program.py", "evaluator.py", "config.yaml", "evolve_local.py")


def scaffold(target_dir: Path, task_name: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "candidates").mkdir(exist_ok=True)
    created, skipped = [], []
    for name in FILES:
        dest = target_dir / name
        if dest.exists():
            skipped.append(str(dest))
        else:
            shutil.copyfile(TEMPLATES / name, dest)
            created.append(str(dest))
    print(json.dumps({"task": task_name, "workspace": str(target_dir.resolve()),
                      "created_files": created, "skipped_existing": skipped}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold an AlphaEvolve workspace")
    parser.add_argument("--target-dir", default="./evolve_workspace", help="directory to create")
    parser.add_argument("--task-name", default="optimization_task", help="name of the optimization task")
    args = parser.parse_args()
    scaffold(Path(args.target_dir), args.task_name)
