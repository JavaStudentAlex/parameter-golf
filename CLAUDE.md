# CLAUDE.md

@AGENTS.md

The file above is the top-level repository contract and is the base instruction
surface for this repository.

For code-writing, review, or refactor tasks, also load
`.github/instructions/code_writing_behavior.instructions.md`.

## Mandatory Tools

- Use `rtk` for every shell command.
- Use `uv` as the sole dependency manager.
- Use `headroom` whenever large output or file content should be compressed
  before reasoning over it.
- Treat `cavveman` as mandatory when the runtime provides it; do not silently
  bypass it if a workflow depends on it.

## Project Alignment

- Prefer surgical edits to `train_gpt.py`, `train_gpt_mlx.py`, and `data/`.
- Treat `records/` as frozen historical submission artifacts unless explicitly
  asked to edit a specific record.
- Re-check the final response for anything missed, omitted, or not verified.
