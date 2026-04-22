---
applyTo: "records/**/*.py"
description: "Conventions for historical submission artifacts under records/."
---

# Records Instructions

## Purpose

This file defines handling rules for historical record artifacts under
`records/`.

## Core Rules

- Treat each record directory as a self-contained historical submission.
- Do not mass-format, reorganize, or deduplicate across records unless that is
  the explicit task.
- Keep record-specific setup, requirements, and README guidance local to the
  record when editing that record.
- Preserve challenge artifact assumptions such as self-contained scripts and
  local requirements.
- Prefer minimal, targeted fixes over aesthetic normalization.

## Mandatory Tooling

- Use `rtk` for shell commands.
- Use `uv` for repository-managed Python execution when practical.
- Use `headroom` for large logs and record outputs.
- Preserve `cavveman` policy if the surrounding workflow depends on it.
