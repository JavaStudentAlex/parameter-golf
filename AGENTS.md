# AGENTS.md
## Purpose: Repository Contract and Execution Conventions

This document defines the top-level repository contract and execution conventions
for agent-based and human-assisted work in this repository.

## Project Overview

`parameter-golf` is the open repository for the Parameter Golf challenge. The
repository contains:
- `train_gpt.py` for the CUDA / PyTorch baseline training script
- `train_gpt_mlx.py` for the Apple Silicon / MLX baseline training script
- `data/` for dataset download, tokenizer export, and retokenization helpers
- `records/` for submitted and historical run artifacts
- `.github/instructions/` for scoped repository guidance
- `.github/agents/` for reusable repository-specific specialist roles
- `.github/skills/` for reusable repository-specific workflows

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.13 |
| Training | PyTorch, torch.distributed |
| Local Apple path | MLX |
| Tokenization / data | sentencepiece, tiktoken, datasets, huggingface-hub |
| Numeric computing | NumPy |
| Dependency Manager | **uv** (strictly) |
| Linting | isort, black, flake8, mypy (via pre-commit + uv run) |
| Historical artifacts | standalone scripts under `records/` |

## Mandatory Tooling

### CLI Proxy (`rtk`)

**All shell commands must be routed through `rtk`.**

```bash
# Correct
rtk git status
rtk uv sync
rtk uv run python train_gpt.py
rtk uv run pre-commit run --files train_gpt.py

# Incorrect
git status
uv sync
python train_gpt.py
```

### Dependency Manager (`uv`)

**`uv` is the sole dependency manager.** Never use `pip install`, `poetry`, or
`conda` directly for repository setup or command execution.

```bash
rtk uv sync
rtk uv sync --group dev
rtk uv run python train_gpt.py
rtk uv run pre-commit run --files train_gpt.py
```

### Context Compression (`headroom`)

**`headroom` is mandatory whenever tool output or file content is large enough to
create avoidable context bloat.**

Use it proactively for:
- long command output
- large diffs or file dumps
- big search results
- logs and JSON payloads

Repository rule:
- compress bulky content before reasoning over it in detail
- retrieve only the slice you need
- do not paste large raw blobs into conversation when `headroom` can carry them

### External Review Tooling (`cavveman`)

**`cavveman` is a mandatory repository policy when the environment provides it.**

Rules:
- do not bypass `cavveman` with ad hoc substitutes when a workflow or user
  expectation depends on it
- if `cavveman` is required by the calling environment but unavailable locally,
  treat that as an environment gap and report it explicitly
- do not invent `cavveman` capabilities or commands that are not grounded in the
  current environment

## Universal Repository Rules

- Treat this file as the top-level repository contract.
- Precedence order is: `AGENTS.md`, then relevant
  `.github/instructions/*.instructions.md`, then `.github/skills/*`.
- For code-writing, review, and refactor tasks, load
  `.github/instructions/code_writing_behavior.instructions.md`.
- Keep type annotations strong for active development code under the root scripts
  and `data/`.
- Prefer the smallest correct change. Do not broaden scope casually.
- Do not invent missing behavior or missing challenge rules. Mark unknowns
  explicitly.
- Historical submissions under `records/` are archival artifacts. Do not apply
  sweeping cleanup, formatting, or refactoring there unless the task explicitly
  targets a specific record.
- Keep `train_gpt.py` and `train_gpt_mlx.py` readable for challenge participants.
- Do not rewrite the repository into a package architecture unless explicitly
  requested.

## Project-Specific Architecture Notes

- Root training scripts are the primary user entry points.
- `data/` owns dataset download, document selection, tokenization, and export
  workflows.
- `records/` contains per-submission self-contained artifacts. Each record should
  stay understandable and runnable within its own folder constraints.
- Repo-wide shared abstractions should be introduced carefully because the
  challenge values script legibility and standalone submission artifacts.

## Instruction Map

- Behavioral code-writing overlay:
  `.github/instructions/code_writing_behavior.instructions.md`
- Active training and data scripts:
  `.github/instructions/python_training.instructions.md`
- Historical record artifacts:
  `.github/instructions/records.instructions.md`
- Quality gates:
  `.github/instructions/python_quality_gates.instructions.md`
- Delegation and subagent policy:
  `.github/instructions/delegation_policy.instructions.md`
- Agent maintenance workflow:
  `.github/instructions/agent_maintenance_workflow.instructions.md`
- Read-only QA overlay:
  `.github/instructions/qa_readonly.instructions.md`

## Repository-Specific Specialists

- Training baseline specialist:
  `.github/agents/training_script_maintainer.agent.md`
- Training run analysis specialist:
  `.github/agents/training_run_analyst.agent.md`
- FineWeb data specialist:
  `.github/agents/fineweb_data_maintainer.agent.md`
- Historical records specialist:
  `.github/agents/records_curator.agent.md`
- FineWeb data workflow skill:
  `.github/skills/fineweb-data-workflow/SKILL.md`
- Historical records workflow skill:
  `.github/skills/records-curation/SKILL.md`

## Mandatory Guardrails

1. Always route shell commands through `rtk`.
2. Always use `uv` as the dependency manager.
3. Always keep `AGENTS.md` loaded as the base contract.
4. Always double-check the final response for missing steps, discrepancies, and
   verification gaps.
5. Never invent benchmark results, validation numbers, artifact sizes, or run
   outcomes.
6. Do not commit or push unless the user explicitly asks for version-control
   actions.

## Delegation Policy

- Delegate only when it materially improves speed, quality, or verification.
- Delegated prompts must include `AGENTS.md` plus the relevant
  `.github/instructions/*.instructions.md` files.
- For code-writing, review, or refactor work, always include
  `.github/instructions/code_writing_behavior.instructions.md`.
- Delegated work must preserve the mandatory `rtk`, `uv`, `headroom`, and
  `cavveman` rules from this file.

@/home/alex/.codex/RTK.md
