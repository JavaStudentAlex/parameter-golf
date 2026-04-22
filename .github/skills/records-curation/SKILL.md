# Records Curation

Work on historical record directories under `records/` without flattening away
their per-record context.

## Mandatory Tooling

- Prefix shell commands with `rtk`
- Use `uv` for repository-managed Python execution when practical
- Use `headroom` for large logs, diffs, and record-file inspections
- Preserve `cavveman` if the surrounding workflow depends on it

## Canonical Scope

- `records/**/README.md`
- `records/**/submission.json`
- `records/**/*.py`
- `records/**/requirements.txt`
- `records/**/setup.sh`
- `records/**/run_*.sh`
- `records/**/train*.log`
- `records/**/RESULTS.md`

## Workflow Checklist

- Scope the task to the specific record directory you are editing.
- Preserve each record as a self-contained artifact bundle with its own local
  setup and reproduction notes.
- When touching metrics or claims, cross-check the touched record's
  `README.md`, `submission.json`, and attached logs for consistency.
- Do not normalize `submission.json` schema across all records. Historical
  entries vary, and preserving local truth matters more than forcing one shape.
- Do not back-propagate record-only experiments into the root baselines unless
  the task explicitly asks for that promotion.
- Prefer per-record validation such as JSON parsing, file-existence checks, and
  `py_compile` on touched Python files over broad repo-wide linting.

## Suggested Checks

Validate touched JSON metadata:

```bash
rtk uv run python -m json.tool records/<track>/<record>/submission.json
```

Syntax-check a touched record script:

```bash
rtk uv run python -m py_compile records/<track>/<record>/train_gpt.py
```

## Verification Guidance

- If a record relies on hardware-, network-, or time-heavy reproduction, state
  that gap explicitly instead of pretending the run was re-executed.
- Treat old logs as evidence, not as targets for cleanup.
