---
description: "Manual overlay for read-only QA, review, and analysis sessions."
---

# QA Read-Only Instructions

## Purpose

Use this file as a lightweight overlay for read-only sessions, QA checks,
reviews, architecture discussion, and exploratory analysis.

## Default Mode

- Default to reading, analysis, and explanation unless edits are explicitly
  requested.
- Prefer targeted reads over loading broad context.
- For review-style tasks, lead with findings, regressions, risks, or missing
  verification before summaries.
- Apply `.github/instructions/code_writing_behavior.instructions.md` as a
  read-only lens when discussing code quality.

## Tooling Expectations

- Even in read-only sessions, route shell commands through `rtk`.
- Use `headroom` when inspection output is large.
- Do not run heavy checks unless the user asked for them or they are needed to
  support a claim.
