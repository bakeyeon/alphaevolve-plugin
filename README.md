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
the grading script, and runs the loop. What you bring is domain knowledge: what a good answer looks like
and which answers are not allowed.

**The idea in one picture.** Evolution here is "try many variations of a recipe, taste each one, keep
the best, repeat". It only works if tasting is automatic, fast, and fair. So ask three questions:

1. **Could a machine grade each attempt, like a multiple-choice exam rather than an essay?**
   The grading may only count, measure, and compare. No human judgment.
2. **Can the grading also check that an answer is allowed?** (No rule broken, same result as a
   trusted slow version.)
3. **Does grading one attempt take seconds, not hours?** Evolution needs tens to hundreds of attempts.

Three yes answers: this plugin fits. Any no: a simpler route is usually better.

### What "a machine can grade it" means

| Problem | How it is graded | Done by |
|---|---|---|
| Placing samples on 96-well plates | count replicate pairs that share a plate; 0 is perfect | counting |
| Booking shared instruments | add up every request's waiting time; lower is better | measuring |
| A slow preprocessing function | time it with a stopwatch, and check its output equals the original | measuring, comparing |
| A classification rule | count correct answers on 500 labeled examples | counting, comparing |
| Packing training batches | count the padding slots | counting |

Hard to grade by machine: "Is this figure pretty?", "Is this abstract persuasive?", "Is this hypothesis
new?" Different people give different scores, and the same person may score differently tomorrow.

**Test it: can the rule become code?** Ask the agent:
*"Write this grading rule as a Python function. Use only counting, measuring, and comparing: no AI
calls and no human judgment."* If it can, a machine can grade it. If the function needs a step like
"ask an AI" or "judge whether it is appropriate", it cannot. The evolution loop needs exactly this
script anyway, so this is the most direct test.

*Thought experiment:* imagine handing the rule to two research assistants. Would they always give the
same number? If not, the rule is still vague.

*Two agents as a warning sign:* you can give the same rule and the same example answers to two
separate agent sessions. If their scores differ, the rule is vague. If they match, that is not proof:
two copies of the same model think alike and can agree even on vague questions such as "is this
abstract persuasive?".

**Split a vague goal into countable parts.** "Is this a good experimental design?" cannot be graded as
it is, but its parts can: equal sample counts per condition (count the difference), controls spread
evenly across days (measure the imbalance), total cost within budget (compare).

You can ask an AI to "rate this from 1 to 10", but those scores wobble, and evolution tends to learn to
please the AI grader instead of solving the problem. Do not use it as the main score.

### Good fits: tasks

| Field | Problem in plain words | Score | Rule that must hold |
|---|---|---|---|
| Lab biology | Place samples on 96-well plates so replicates and controls are spread out | fewer constraint violations, better balance | every sample placed exactly once |
| Psychology | Order stimuli for each participant so no item is always early or late (counterbalancing) | position and order imbalance | every participant sees every item once |
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

### Good fits: research experiments that look for a rule in data

Evolution can also search for an explanation: a small, readable program (a set of rules, a formula,
or a simple simulation) that reproduces your data. The program is the hypothesis, and you can read it.
One principle makes this work:

**Grade only on data the program has not seen.** Hold part of the data back, by time or by item, and
grade the program on that part alone. Otherwise evolution memorizes your data and the score means
nothing. A forecast cannot be graded against a future that has not happened, so pretend an earlier
year is "now" and grade the forecast against what really happened after it (this is called backtesting).

**Worked example: how language varieties diverge, and where they are heading.**
Turn the question into a gradable one. Two versions:

1. **Sound-change rules.** Data: older word forms and their attested forms in several dialects.
   Evolve: an ordered list of sound-change rules that turns the old forms into each dialect's forms.
   Grade: how many letters are wrong (edit distance) between predicted and attested forms, on words
   held back from training. Rule: only general sound rules, no per-word exceptions, so the program cannot
   simply store the answers. What you learn: a candidate rule order for each dialect, and the words that
   resist it, which may point to borrowing.
2. **Trends in variant use.** Data: how often each competing variant (for example two endings) appears
   per decade and region, from corpora or surveys. Evolve: a small model of change, such as a formula or a
   simulation of speakers who copy neighbors and prestige forms. Grade: fit on 1950 to 1990, predict 2000
   to 2020, and measure the error against what was observed. Then run the best model forward to project
   the trend.

| Field | Evolve | Grade on held-back data |
|---|---|---|
| Linguistics | a rule that guesses a speaker's dialect from a word list | accuracy on held-back speakers |
| Ecology | a population-growth rule with weather as input | error when predicting later years of counts |
| Epidemiology | a short-term case-forecasting rule | backtest error on past weeks |

Say these limits out loud in any write-up:
- **A good fit does not prove the cause.** Several different programs may fit equally well. Compare the
  top few, not only the winner, and judge them with your domain knowledge.
- **Little data means easy overfitting.** Keep the program small and the held-back data untouched.
- **Forecasts get less certain the further they go.** Report them as scenarios together with the
  backtest error, not as facts.

### Not needed: use something simpler

| Situation | Why evolution does not help | Use instead |
|---|---|---|
| A standard task with a known method (sorting, shortest path, linear regression, alignment) | Experts already found the best method | an existing library; ask the agent which one |
| Tuning a few numbers (learning rate, thresholds) | Searching numbers, not code | grid search or a tuner such as Optuna |
| Testing whether an effect is real (group A vs group B) | That is a statistics question, not a search | a standard statistical test |
| No automatic score (writing quality, figure design, "is this hypothesis interesting") | Nothing to compare attempts by | ask the agent directly, judge it yourself |
| Each evaluation takes minutes to hours (a full training run, an overnight simulation, a wet-lab experiment) | Hundreds of attempts would take weeks | shrink to a fast proxy problem first, or optimize by hand |
| The code is wrong or crashes | Evolution improves working code; it does not debug | ask the agent to fix the bug |
| A script you will run once | Saving seconds does not matter | the simplest version that works |

### Starting prompt: does it fit my research?

Not sure? Paste this into Claude Code (or any agent that can read web pages) and fill in the brackets.
It works whether or not the plugin is installed.

```text
Read https://github.com/bakeyeon/alphaevolve-plugin (the README and skills/alphaevolve/SKILL.md).
Then analyze whether any part of my research could use this plugin.

My research: [what you study, what data you have, what is slow, repetitive, or hard to decide]

Answer in this order:
1. Candidate parts: each piece of my work that could become a program to evolve.
2. For each part, the three-question check from the README (machine-gradable like a
   multiple-choice exam? can the grading check the rules? seconds per grading?), yes or no with a reason.
3. For each "yes": what the program would be, the score, the rules, and which data to hold back.
4. For each "no": why, and what I should use instead.
5. Your recommendation: the one best place to start, or "this plugin is not a good fit".
Use plain language; I am not a programmer. Do not write code yet.
```

Variations, used in place of the "My research" line:
- **You have code:** *"My analysis code is in [folder]. Find the slow parts and the hand-made rules or heuristics, then run the same check on each."*
- **You have a paper or draft:** *"My draft is [file]. Look at the methods section and run the same check on each step."*
- **Quick answer:** *"In three sentences, using the README's three-question check: would this plugin help with [task]?"*

### How a non-programmer starts

1. Describe the problem: *"I assign 300 samples to 96-well plates. Replicates of one sample must not
   share a plate, and each plate needs 4 controls. Make the plates as balanced as possible."*
2. The agent writes a simple, obviously correct version (L1) and a grading script.
3. **Check the grading script yourself.** Ask the agent to show a few example answers with their scores
   and rule checks, and ask whether the rule could be written as code. If a bad answer gets a good score, say so: the
   score is what evolution chases.
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

## Acknowledgements

- Inspired by the evolutionary coding agent architecture described in **Google DeepMind's [AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)** research ([`alphaevolve_results`](https://github.com/google-deepmind/alphaevolve_results)).
- Workspace templates (`# EVOLVE-BLOCK`, `evaluator.py`, `config.yaml`) are designed to interoperate with **[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve)** by Algorithmic SuperIntelligence Labs.
- Built for use with **[Google Antigravity](https://antigravity.google)** and **[Claude Code](https://code.claude.com/docs/en/overview)**.

> *Disclaimer: This is an independent community plugin and is not affiliated with or endorsed by Google DeepMind. Released completely free and open-source under the [MIT License](LICENSE) with no plans for monetization.*
