---
applyTo: "**/*.py"
description: "Python quality gate policy for active repository code."
---

# Python Quality Gates

## Purpose and Scope

This file defines the verification policy for Python changes in this repository.

Primary scope:
- `train_gpt.py`
- `train_gpt_mlx.py`
- `data/**/*.py`

Historical `records/**/*.py` files follow repository guardrails but are not part
of the default active-code lint surface unless the task explicitly targets them.

## Mandatory Tooling

All commands must go through `rtk`. All Python execution must use `uv`.

## Quality Gate Skills

### python-linting
- Path: `.github/skills/python-linting/SKILL.md`
- Purpose: code quality and type-safety verification
- Gates: isort, black, flake8, mypy

### python-testing
- Path: `.github/skills/python-testing/SKILL.md`
- Purpose: lightweight smoke verification for executable scripts

## Quality Gates Policy

For Python code changes in the active development surface, linting is mandatory
before the work is considered complete.

## Default Lint Gate Set

Run from repo root:

```bash
rtk uv run pre-commit run isort --files train_gpt.py train_gpt_mlx.py data/cached_challenge_fineweb.py data/download_hf_docs_and_tokenize.py
rtk uv run pre-commit run black --files train_gpt.py train_gpt_mlx.py data/cached_challenge_fineweb.py data/download_hf_docs_and_tokenize.py
rtk uv run pre-commit run flake8 --files train_gpt.py train_gpt_mlx.py data/cached_challenge_fineweb.py data/download_hf_docs_and_tokenize.py
rtk uv run pre-commit run mypy --files train_gpt.py train_gpt_mlx.py data/cached_challenge_fineweb.py data/download_hf_docs_and_tokenize.py
```

Use the changed-file subset instead of hardcoding these filenames when the task
touches a narrower slice.

## Smoke Verification

There is no established repo-wide pytest suite yet. When code changes affect
executable scripts, run the lightest meaningful smoke check for the changed path
and report any gaps explicitly.

## Notes

- Never invent passing results.
- If environment limits block a gate, report that clearly.
- Do not claim repo-wide cleanliness from a changed-file-only lint run.
