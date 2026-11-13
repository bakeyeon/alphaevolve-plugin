# AlphaEvolve Plugin

**English** | [한국어](README.ko.md)

An evolutionary algorithm discovery and code optimization plugin modeled on Google DeepMind's **AlphaEvolve** and the open-source **OpenEvolve**.
Works with Claude Code and Antigravity.

## Install

**Claude Code**
```
/plugin marketplace add bakeyeon/alphaevolve-plugin
/plugin install alphaevolve@alphaevolve-plugin
```

**Antigravity**: add this repository as a plugin. It uses the root `plugin.json`.

## Features

1. **Agent-driven evolution loop (Mode A)**
   - No extra package or API key: the agent proposes mutations itself.
   - `evolve_local.py` scores each candidate and maintains `archive.json` and `best_program.py`.
   - Four commands: `init`, `sample`, `evaluate`, `status`.
2. **OpenEvolve CLI integration (Mode B)**
   - Scaffolds `initial_program.py`, `evaluator.py`, and `config.yaml` that work directly with `pip install openevolve`.
3. **A trustworthy evaluator template**
   - Checks correctness against a reference solver (exact DP).
   - Tests on 40 seeded random instances plus edge cases.
   - Runs each candidate in its own process with a time limit.
   - Keeps `combined_score` quality-only, so the same program always gets the same score. Runtime is recorded separately as a median.

## Recommended path: three levels, then evolve

1. **L1 baseline**: a direct, obviously correct implementation of the definition. It becomes the evaluator's reference.
2. **L2 clean**: a readable, practical algorithm.
3. **L3 optimized**: the best approach you can derive yourself.
4. **Evolve**: only when you want to search beyond L3. The problem needs a score that code can compute.

## Example prompts

- *"Evolve and optimize this algorithm AlphaEvolve-style."*
- *"Set up an AlphaEvolve / OpenEvolve evaluator and initial program for my optimization problem."*
- *"Evolve this function to maximize its heuristic score."*

## Layout
```
skills/alphaevolve/SKILL.md                     skill description and workflow
skills/alphaevolve/scripts/scaffold_evolve.py   creates a workspace (never overwrites existing files)
skills/alphaevolve/scripts/templates/           initial_program.py, evaluator.py, config.yaml, evolve_local.py
```

See [CHANGELOG.md](CHANGELOG.md) for release notes.
