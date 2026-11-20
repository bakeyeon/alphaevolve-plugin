# Changelog

## 1.4.2 (2026-11-20)

- README: adds a beta notice at the top (English and Korean).
- README: adds "How is this different from deep learning?" comparing neural-network weights with readable evolved code for junior researchers (English and Korean).

## 1.4.1 (2026-11-20)

- README, `SKILL.md`, `evaluator.py` comment: describe `BLIND_MODE` as a leak guard that closes one path
  (error messages), not GDPR or IRB compliance. Note that a Read deny rule does not block Bash, so the real
  file belongs outside the project, and that an offline Mode B setup needs `api_base`, model names and
  `api_key` changed together. English and Korean.

## 1.4.0 (2026-11-20)

- `evaluator.py`: enables **`BLIND_MODE = True` by default** for GDPR / private-corpus protection. Crash reports now strip exception message strings and raw `stderr` (reporting only exception type and file/line location), and constraint failures omit raw data values so corpus text or participant data cannot leak into the cloud agent context.
- `SKILL.md` & README: adds a dedicated guide for working with private or GDPR/IRB-regulated datasets (using a 3-row synthetic schema sample, keeping `BLIND_MODE = True`, and optional air-gapped local LLM execution via Mode B).

## 1.3.0 (2026-11-20)

- `evaluator.py` & `evolve_local.py`: adds built-in **held-out verification** (`HELD_OUT_SEED`, `evaluate(path, held_out=True)`, `evaluator.py --held-out`, and `evolve_local.py status --held-out`) so `best_program.py` can be tested on data never seen during evolution.
- `evaluator.py`: adds `MAX_CODE_CHARS` guard against lookup-table memorisation, plus guidance on loading external corpus/CSV/TSV datasets directly inside `_RUNNER` instead of piping large files over `stdin`.
- `SKILL.md`: adds evaluator rules for held-out verification, anti-memorisation size caps, and corpus file loading.
- README & `LICENSE`: adds MIT License and Acknowledgements section (AlphaEvolve, OpenEvolve, Antigravity, Claude Code) clarifying that this is a free, independent community plugin (English and Korean).
- README: the main grading check is now "ask the agent to write the grading rule as code, with no AI
  calls or human judgment". The two-assistant test stays as a thought experiment, and comparing two
  agent sessions is described as a warning sign only, since agreement between copies of one model is not proof.

## 1.2.0 (2026-11-16)

- README: adds "Is this plugin right for my problem?" with a three-question check, good-fit and
  not-needed use cases across fields, guidance for large training code, and a start guide for
  non-programmers (English and Korean).
- README: the fit check now asks whether a machine could grade each attempt like a multiple-choice
  exam, with grading examples, the two-assistant test, and research-experiment examples (held-back
  data, backtesting, language divergence) with their limits.
- README: adds a copy-paste starting prompt that checks whether the plugin fits your research,
  with variations for code, drafts, and quick answers.
- README: adds "Local evolve code at a glance", a function-by-function overview of the Mode A scripts.
- `config.yaml`: OpenEvolve (Mode B) now uses the Claude API through `ANTHROPIC_API_KEY`, with
  settings Claude accepts and comments on cost and setup.
  **Note:** Mode B workspaces created from this template now need `ANTHROPIC_API_KEY`. To keep another
  provider such as Gemini, change `api_base`, the model names and `api_key` together.
  Existing workspaces keep their own `config.yaml` and are not affected.
- Explanatory comments in all skill scripts.

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
