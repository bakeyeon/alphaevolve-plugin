# Changelog

## 1.1.0 (2026-11-13)

### Evaluator
- Checks correctness against an exact dynamic-programming reference on 40 seeded random instances plus 5 edge cases. Before, it used 3 hard-coded cases, which let evolution memorize answers.
- Runs each candidate in a separate process with a 20-second limit, so an infinite loop or crash no longer stalls the run.
- `combined_score` now reflects solution quality only, so it is reproducible. Runtime is reported separately as the median of repeated `solve()` calls, excluding import time.
- Candidate `print` output no longer corrupts results.
- Adds the missing `import json` in the evaluator's command-line entry point.

### Archive tool (`evolve_local.py`)
- Adds the `sample` command that `SKILL.md` already referenced. It returns top scorers (exploit) and diverse valid picks (explore).
- `evaluate` now reports the score change against the parent (`delta_vs_parent`).

### Structure and docs
- Templates moved out of string literals into `skills/alphaevolve/scripts/templates/`, so they can be read and tested directly.
- `SKILL.md` and the README work for Claude Code as well as Antigravity, with install steps and evaluator rules.
- Adds the recommended L1 → L2 → L3 → evolve path.
- English README; the Korean README is now `README.ko.md`.

## 1.0.0 (2026-11-13)
- First release: AlphaEvolve-style skill with an agent-driven loop (Mode A), OpenEvolve scaffolding (Mode B), and a 0/1 knapsack example.
