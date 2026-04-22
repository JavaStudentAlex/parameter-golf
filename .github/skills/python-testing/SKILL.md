# Python Testing

Run lightweight smoke verification for active repository scripts.

## Mandatory Tooling

- Prefix shell commands with `rtk`
- Use `uv` for execution
- Use `headroom` if output becomes large

## Suggested Smoke Checks

Syntax check changed executable scripts:

```bash
rtk uv run python -m py_compile train_gpt.py train_gpt_mlx.py data/cached_challenge_fineweb.py data/download_hf_docs_and_tokenize.py
```

Script help / argument parsing checks when relevant:

```bash
rtk uv run python data/cached_challenge_fineweb.py --help
rtk uv run python data/download_hf_docs_and_tokenize.py --help
```

## Scope Guidance

- Prefer the lightest verification that proves the claim.
- If a true runtime smoke test depends on large datasets or GPUs, report that as
  a verification gap instead of pretending coverage exists.
