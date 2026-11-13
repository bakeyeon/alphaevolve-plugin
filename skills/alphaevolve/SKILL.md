---
name: alphaevolve
description: >-
  Evolutionary coding and autonomous algorithm discovery/optimization inspired by
  Google DeepMind's AlphaEvolve and OpenEvolve. Use when the user mentions
  "AlphaEvolve", "OpenEvolve", "evolutionary coding", "evolve algorithm",
  "MAP-Elites code optimization", or wants to iteratively evolve, benchmark, and
  discover higher-performing algorithms or heuristics against an automated evaluator.
---

# AlphaEvolve Skill

AlphaEvolve-style evolutionary algorithm discovery for coding agents (Claude Code, Antigravity, and similar). Two modes:

1. **Mode A, agent-driven loop** (no extra API key): you, the agent, propose mutations; `evolve_local.py` scores them with `evaluator.py` and keeps the archive.
2. **Mode B, OpenEvolve CLI**: scaffolds files that the `openevolve` package runs for long autonomous runs (needs an LLM API key).

## First, check that evolution fits

Evolution only helps when the problem has a **score a program can compute**: heuristic quality, runtime, the size of a construction, a bound. If the task has one exact answer and a known optimal algorithm (for example Fibonacci by fast doubling), say so and implement that directly instead.

A good ladder before evolving:
1. **L1 baseline**: a direct, obviously correct implementation (slow is fine). Use it as the evaluator's **reference oracle**.
2. **L2 clean**: a readable, practical algorithm.
3. **L3 optimized**: the best known approach you can derive.
4. **Evolve** from L2 or L3 only when you want to search beyond what you can derive.

## Core architecture

1. **Target program (`initial_program.py`)**: only the region between markers is mutated.
   ```python
   # EVOLVE-BLOCK-START
   def solve(problem_input):
       ...
   # EVOLVE-BLOCK-END
   ```
2. **Evaluator (`evaluator.py`)**: `evaluate(program_path) -> dict` with a primary `combined_score` (higher is better) plus features such as `runtime_ms` and `complexity` for MAP-Elites.
3. **Archive (`archive.json`)**: every candidate with its parent, rationale and metrics. `best_program.py` always holds the current best valid candidate.

## Evaluator rules (the template follows all of them; keep them when adapting)

- **Judge correctness against a trusted reference** (exact solver or the L1 baseline). Invalid output scores 0.
- **Use many seeded random instances plus edge cases**, not a few hard-coded ones. Otherwise evolution memorises answers.
- **Run each candidate in a separate process with a hard timeout.** One infinite loop must not stall the run.
- **Keep `combined_score` deterministic.** Report runtime separately (median of repeats, import excluded) instead of mixing noisy timings into the score.
- **Never edit the evaluator to make a candidate pass.** If the evaluator is wrong, fix it, then re-score the whole archive.

## Workflow

### Step 1: Scaffold
```bash
python "<path-to-this-skill>/scripts/scaffold_evolve.py" --target-dir ./evolve_workspace --task-name my_optimization
```
The templates are a 0/1 knapsack example (`scripts/templates/`). Rewrite `initial_program.py`, `make_instances`, `reference_solve` and the scoring in `evaluator.py` for the user's problem. Existing files are never overwritten.

### Step 2: Verify the baseline
```bash
python ./evolve_workspace/evaluator.py ./evolve_workspace/initial_program.py
```
Check that the baseline is valid, that running it twice gives the same `combined_score`, and that one evaluation finishes in seconds.

### Step 3: Evolve

#### Mode A: agent-driven
```bash
python ./evolve_workspace/evolve_local.py init     --workspace ./evolve_workspace
python ./evolve_workspace/evolve_local.py sample   --workspace ./evolve_workspace -k 3
python ./evolve_workspace/evolve_local.py evaluate --workspace ./evolve_workspace \
    --candidate ./evolve_workspace/candidates/next.py --parent-id gen_000 \
    --rationale "Replaced greedy selection with DP over capacity"
python ./evolve_workspace/evolve_local.py status   --workspace ./evolve_workspace
```
Each generation:
1. `sample` returns top scorers (`exploit`) and a few diverse valid picks (`explore`). Read the parent code and its metrics.
2. Write one child that changes **one idea**: an algorithmic change, a mathematical insight, or a structural rewrite of the EVOLVE-BLOCK. Write the rationale before running it.
3. `evaluate` it, read `delta_vs_parent` and any `error`, and use failures as feedback for the next mutation.
4. If the agent supports subagents, generate several children from different parents in parallel, then evaluate them one by one.

Stop when the score plateaus for several generations or hits the reference optimum. Then present a generation table (`status`) and explain **why** the best program works. Flag improvements you cannot explain: they may not generalise beyond the test instances.

#### Mode B: OpenEvolve CLI
```bash
pip install openevolve
python -m openevolve.cli ./evolve_workspace/initial_program.py ./evolve_workspace/evaluator.py \
    --config ./evolve_workspace/config.yaml --iterations 50
```
Needs an API key for an OpenAI-compatible endpoint (for example `OPENAI_API_KEY`, or a Gemini key with the OpenAI-compatible base URL in `config.yaml`). Ask the user to set it in their environment; never write keys into files. Option names in `config.yaml` can differ between OpenEvolve versions, so check them against the installed version.

## Reference repositories
- DeepMind results: `https://github.com/google-deepmind/alphaevolve_results`
- DeepMind problem repository: `https://github.com/google-deepmind/alphaevolve_repository_of_problems`
- Google Cloud sample: `https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud`
- OpenEvolve: `https://github.com/algorithmicsuperintelligence/openevolve`
