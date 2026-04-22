# Python Linting

Run lint and type-check gates for active repository code.

## Mandatory Tooling

- Prefix shell commands with `rtk`
- Use `uv` for execution
- Use `headroom` if output becomes large

## Default Commands

```bash
rtk uv run pre-commit run isort --files <changed-python-files>
rtk uv run pre-commit run black --files <changed-python-files>
rtk uv run pre-commit run flake8 --files <changed-python-files>
rtk uv run pre-commit run mypy --files <changed-python-files>
```

## Scope Guidance

- Default scope is `train_gpt.py`, `train_gpt_mlx.py`, and `data/**/*.py`.
- Treat `records/**/*.py` as opt-in unless the task explicitly edits them.
