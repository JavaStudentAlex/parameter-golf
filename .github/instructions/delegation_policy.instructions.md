---
description: "Delegation, subagent spawning, and repository overlay policy."
---

# Delegation Policy

## Purpose

This file defines repository policy for delegation, subagent spawning, and reuse
of repository guidance under `.github/`.

## Mandatory Tooling

Delegated agents must:
- use `rtk` for all shell commands
- use `uv` as the dependency manager
- use `headroom` for large outputs
- preserve `cavveman` requirements when the runtime provides it

## Core Rules

- Keep `AGENTS.md` as the mandatory base contract for delegated work.
- Add the relevant `.github/instructions/*.instructions.md` files based on task
  scope.
- Include `.github/instructions/code_writing_behavior.instructions.md` whenever
  the task writes, reviews, or refactors code.
- Keep delegated prompts grounded in actual repository files and constraints.
- Do not use delegation to hide uncertainty or skip verification.

## Spawn Decision Rule

Delegate when:
- work is non-trivial and parallelizable
- a sidecar verification lane can run independently
- documentation or repo-governance work is cleanly separable

Keep work local when:
- the task is a small read or quick edit
- the next step is tightly coupled and blocking
- delegation overhead is higher than the work itself
