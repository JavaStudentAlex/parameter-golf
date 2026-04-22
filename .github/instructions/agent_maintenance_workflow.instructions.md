---
applyTo: ".github/agents/**/*.agent.md"
description: "Standards and workflow for maintaining custom agents in this repository."
---

# Agent Maintenance Workflow and Standards

## Canonical Paths in This Repository

- Repo-wide instructions and guardrails: `AGENTS.md`
- Path-scoped instructions: `.github/instructions/*.instructions.md`
- Custom agents: `.github/agents/*.agent.md`
- Reusable skills: `.github/skills/*/SKILL.md`

## Quality Standards

### Agent Frontmatter Requirements

Each `.agent.md` file should include valid YAML frontmatter with:
- `name`
- `description`
- `tools`

### Agent Content Structure

Each agent should include:
- role overview
- core competencies
- responsibilities
- scope boundaries

## Repository Rules

- Agent docs must preserve the mandatory `rtk`, `uv`, `headroom`, and
  `cavveman` policy from `AGENTS.md`.
- Keep agent files concise and specific.
- Do not claim runtime tools or permissions that are not grounded in the actual
  environment.
