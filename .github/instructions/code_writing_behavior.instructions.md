---
description: "Behavioral overlay for code writing, review, and refactor tasks."
---

# Code Writing Behavior

## Purpose

This file defines the repository's behavioral expectations for day-to-day
engineering work.

Use it when a task involves:
- writing or editing code
- reviewing code
- refactoring or cleanup work

## Core Behavior

- Make assumptions explicit when they materially change the solution.
- Prefer the smallest correct change. Avoid speculative abstractions and
  broad refactors.
- Keep edits surgical and tied to the request.
- Match local style and current challenge constraints unless a narrower
  instruction says otherwise.
- If you notice unrelated issues, call them out separately instead of
  expanding the diff.

## Execution Pattern

Before implementing:
- state the working assumptions when needed
- identify the smallest viable path
- define what will verify success

During implementation:
- touch only the files needed for the task
- remove imports, variables, or helpers made unused by your own changes
- avoid opportunistic cleanup in historical `records/` artifacts

Before completion:
- verify the claimed outcome with the lightest sufficient evidence
- report open questions, constraints, and gaps explicitly

## Project-Specific Notes

- `train_gpt.py` and `train_gpt_mlx.py` are participant-facing baselines, so
  readability matters.
- `records/` folders are historical submission artifacts. Preserve their
  self-contained structure and challenge assumptions.
- If the simplest solution is to do less, do less.
