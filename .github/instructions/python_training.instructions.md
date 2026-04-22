---
description: "Conventions for active training scripts and data helpers."
---

# Python Training Instructions

## Scope

These instructions cover active development code in:
- `train_gpt.py`
- `train_gpt_mlx.py`
- `data/**/*.py`

## Mandatory Tooling

All shell commands must go through `rtk`.
All Python execution and environment management must go through `uv`.

## Behavioral Overlay

For code-writing and refactor tasks, also apply
`.github/instructions/code_writing_behavior.instructions.md`.

## Core Rules

- Keep public and helper functions typed.
- Prefer straightforward script structure over premature modularization.
- Keep environment-variable knobs discoverable and documented near where they are
  used.
- Preserve challenge-facing behavior and baseline readability.
- Keep comments focused on challenge-specific logic, not generic Python syntax.
- Avoid hidden side effects and silent behavior changes in training loops,
  evaluation paths, or artifact accounting.

## Data and Training Constraints

- Data-path assumptions must stay explicit and local.
- Validation behavior, artifact-size accounting, and tokenizer-related logic are
  load-bearing. Treat them conservatively.
- Do not add new dependency managers, orchestration layers, or packaging
  indirection unless explicitly requested.
