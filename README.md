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

## Is this plugin right for my problem?

You do not need to be a programmer. You describe the problem in plain words; the agent writes the code,
the scoring script, and runs the loop. What you bring is domain knowledge: what a good answer looks like
and which answers are not allowed.

**The idea in one picture.** Evolution here is "try many variations of a recipe, taste each one, keep
the best, repeat". It only works if tasting is automatic, fast, and fair. So ask three questions:

1. **Can a short script give each attempt a number score?** (Higher is better: fewer wasted slots,
   lower cost, faster run, higher accuracy on a fixed test set.)
2. **Can that script check that an answer is allowed?** (No rule broken, same result as a trusted
   slow version.)
3. **Does one scoring run take seconds, not hours?** Evolution needs tens to hundreds of attempts.

Three yes answers: this plugin fits. Any no: a simpler route is usually better.

### Good fits

| Field | Problem in plain words | Score | Rule that must hold |
|---|---|---|---|
| Lab biology | Place samples on 96-well plates so replicates and controls are spread out | fewer constraint violations, better balance | every sample placed exactly once |
| Any lab | Book shared instruments (sequencer, microscope) for many requests | total waiting time | no double booking, deadlines met |
| Linguistics, NLP | A text-cleaning or tokenizing function is too slow on a large corpus | run time on a fixed sample | output identical to the current function |
| Bioinformatics | A custom sequence-scoring function is the bottleneck of a pipeline | run time, memory | same scores as the original |
| Operations, logistics | Route field-survey visits or deliveries | total distance | every site visited, time windows kept |
| ML training | Pack variable-length sequences into batches with as little padding as possible | padding fraction, batches per epoch | every sequence used once, batch size limit |
| ML training | Speed up a data-preprocessing step or one custom layer | run time and peak memory on a fixed small input | same output as the reference |

**Large training code.** You cannot evolve a whole training run: one evaluation would take hours.
Instead, cut out the slow piece (a preprocessing step, a batching rule, one custom operation), give it a
fixed small input, and score its speed and memory in seconds while checking it still gives the same
result. The evaluator template measures run time; for memory, ask the agent to add a peak-memory
metric (for example with `tracemalloc`, or `torch.cuda.max_memory_allocated` on a GPU).
Then put the improved piece back into the full training code and confirm the gain there.

### Not needed, use something simpler

| Situation | Why evolution does not help | Use instead |
|---|---|---|
| A standard task with a known method (sorting, shortest path, linear regression, alignment) | Experts already found the best method | an existing library; ask the agent which one |
| Tuning a few numbers (learning rate, thresholds) | Searching numbers, not code | grid search or a tuner such as Optuna |
| No automatic score (writing quality, figure design, "is this hypothesis interesting") | Nothing to compare attempts by | ask the agent directly, judge it yourself |
| Each evaluation takes minutes to hours (a full training run, an overnight simulation, a wet-lab experiment) | Hundreds of attempts would take weeks | shrink to a fast proxy problem first, or optimize by hand |
| The code is wrong or crashes | Evolution improves working code; it does not debug | ask the agent to fix the bug |
| A script you will run once | Saving seconds does not matter | the simplest version that works |

### How a non-programmer starts

1. Describe the problem: *"I assign 300 samples to 96-well plates. Replicates of one sample must not
   share a plate, and each plate needs 4 controls. Make the plates as balanced as possible."*
2. The agent writes a simple, obviously correct version (L1) and a scoring script.
3. **Check the scoring script yourself.** Ask the agent to show a few example answers with their scores
   and rule checks. If a bad answer gets a good score, say so: the score is what evolution chases.
4. Run the Mode A loop and read `best_program.py` and the score history with the agent.

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

## Local evolve code at a glance

In Mode A, three scripts share the work: `scaffold_evolve.py` creates the workspace once,
`evaluator.py` scores one program, and `evolve_local.py` keeps the history of every attempt and
decides which one is best. The agent writes new programs; these scripts only judge and record them.

**`scaffold_evolve.py`**
- `scaffold(target_dir, task_name)`: copies the four template files into a new workspace and creates
  `candidates/`. Skips files that already exist, so your edits are never overwritten.

**`evaluator.py`**
- `make_instances(seed, n)`: builds the test set, n seeded random problems plus fixed edge cases.
  The same seed means every candidate is tested on the same problems.
- `reference_solve(items, capacity)`: the trusted slow solver (exact DP) that gives the true optimum.
- `evaluate(program_path)`: runs one candidate in a separate process with a time limit, rejects any
  answer that breaks a rule, and returns metrics: `combined_score`, `valid`, `optimality_ratio`,
  `optimal_fraction`, `runtime_ms`, `complexity`.
- `_fail(error)`: the metrics for a rejected candidate (score 0, `valid` 0, with the reason).

**`evolve_local.py`** (commands)
- `init` (`cmd_init`): scores `initial_program.py` as `gen_000` and starts a new `archive.json`.
- `sample` (`cmd_sample`): suggests parents to mutate next: the top scorers (exploit) plus up to two
  programs of different sizes (explore), so the search does not get stuck on one idea.
- `evaluate` (`cmd_evaluate`): copies a new candidate into `candidates/`, scores it, records it with
  its parent and rationale, and reports `delta_vs_parent` (positive means the change helped).
- `status` (`cmd_status`): shows the best generation and a one-line history of all generations.

**`evolve_local.py`** (helpers)
- `load_evaluator(workspace)`: imports the workspace's own `evaluator.py`.
- `load_archive` / `save_archive`: read and write `archive.json`.
- `_update_best(workspace, archive)`: finds the highest-scoring valid generation and copies it to
  `best_program.py`. Ties go to the earlier, usually simpler, program.

See [CHANGELOG.md](CHANGELOG.md) for release notes.
