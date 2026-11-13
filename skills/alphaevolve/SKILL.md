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

This skill enables **AlphaEvolve-style evolutionary algorithm discovery and optimization** in Antigravity. It supports two execution modes depending on the user's environment and preference:

1. **Native Agent-Driven AlphaEvolve Loop** (Zero external API key setup required — uses Antigravity's own reasoning, subagents, and sandbox test runner to maintain an archive of candidate programs and evolve `# EVOLVE-BLOCK` regions).
2. **OpenEvolve / Google Cloud AlphaEvolve Integration** (Scaffolds and runs `openevolve` or `alphaevolve-on-googlecloud` pipelines with `initial_program.py`, `evaluator.py`, and `config.yaml`).

---

## Core Architecture (AlphaEvolve Pattern)

Every AlphaEvolve workflow consists of three decoupled components:

1. **Target Program (`initial_program.py`)**:
   Contains the baseline algorithm with explicit evolution boundaries:
   ```python
   # EVOLVE-BLOCK-START
   def solve(problem_input):
       # Baseline heuristic or algorithm to be evolved
       ...
   # EVOLVE-BLOCK-END
   ```
   Code outside the markers remains pinned unless the user asks for full-file evolution.

2. **Automated Evaluator (`evaluator.py`)**:
   A deterministic script or function `evaluate(program_path: str) -> dict` that dynamically imports the candidate program, runs correctness checks and benchmarks across test cases (with strict timeouts), and returns quantitative metrics including a primary `combined_score` (higher is better) and optional behavioral descriptors (e.g., `complexity`, `runtime_ms`, `memory_kb`) for quality-diversity (MAP-Elites) archiving.

3. **Evolutionary Loop & Population Archive**:
   Maintains a population/archive of evaluated candidates (`archive.json`), selects high-performing and diverse parent candidates (exploitation + exploration), synthesizes mutations or crossovers informed by evaluation feedback/stack traces, and verifies every child via `evaluator.py`.

---

## Workflow Step-by-Step

### Step 1: Scaffold the Evolutionary Workspace

Run the bundled scaffolding helper script [scaffold_evolve.py](./scripts/scaffold_evolve.py) (located in `./scripts/scaffold_evolve.py` relative to this `SKILL.md` file) to generate a structured AlphaEvolve directory (`initial_program.py`, `evaluator.py`, `config.yaml`, and `evolve_local.py`):

```bash
python "<path-to-this-skill>/scripts/scaffold_evolve.py" --target-dir ./evolve_workspace --task-name my_optimization
```

Then tailor `initial_program.py` and `evaluator.py` to the user's specific problem (e.g., combinatorial optimization, kernel tuning, mathematical bounds, heuristic scheduling, or prompt/code optimization).

### Step 2: Verify the Baseline Evaluator

Before starting evolution, always run `evaluator.py` against `initial_program.py` to verify:
- The baseline passes correctness checks.
- The `combined_score` metric is deterministic and reproducible.
- Execution completes quickly enough for multi-generation evaluation.

```powershell
python ./evolve_workspace/evolve_local.py status --workspace ./evolve_workspace
```

### Step 3: Run the Evolution Loop

Choose either **Mode A (Agent-Driven Evolution)** or **Mode B (OpenEvolve CLI)**:

#### Mode A: Native Agent-Driven Evolution (Recommended inside Antigravity)
1. Initialize the archive with the baseline candidate:
   ```powershell
   python ./evolve_workspace/evolve_local.py init --workspace ./evolve_workspace
   ```
2. For each generation (or in parallel using `invoke_subagent` with `self`):
   - Inspect top-performing and diverse parents from `archive.json` (`evolve_local.py sample`).
   - Propose an algorithmic improvement, mathematical insight, or structural mutation to the `# EVOLVE-BLOCK` region, saving it to a candidate file.
   - Register and evaluate the candidate:
     ```powershell
     python ./evolve_workspace/evolve_local.py evaluate --workspace ./evolve_workspace --candidate ./evolve_workspace/candidates/gen_01.py --rationale "Replaced greedy selection with 2-opt local search"
     ```
   - Review the score delta, runtime metrics, and failure diagnostics.
3. Export the best discovered program back to `best_program.py` and present a summary table of generation progression.

#### Mode B: OpenEvolve CLI (`openevolve`)
If the user wants autonomous multi-hundred-iteration background runs via the `openevolve` package:
1. Check or install `openevolve`:
   ```powershell
   pip install openevolve
   ```
2. Ensure `OPENAI_API_KEY` or `GEMINI_API_KEY` is configured (use the `credentials` skill if needed).
3. Launch OpenEvolve:
   ```powershell
   python -m openevolve.cli ./evolve_workspace/initial_program.py ./evolve_workspace/evaluator.py --config ./evolve_workspace/config.yaml --iterations 50
   ```

---

## Reference Repositories

- **DeepMind Official Results & Benchmarks**:
  - `https://github.com/google-deepmind/alphaevolve_results`
  - `https://github.com/google-deepmind/alphaevolve_repository_of_problems`
- **Google Cloud AlphaEvolve Sample**:
  - `https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud`
- **OpenEvolve (Open-Source Implementation)**:
  - `https://github.com/algorithmicsuperintelligence/openevolve`
