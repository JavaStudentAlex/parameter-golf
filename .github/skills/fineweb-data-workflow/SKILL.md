# FineWeb Data Workflow

Work safely on the manifest-driven FineWeb download and retokenization pipeline
under `data/`.

## Mandatory Tooling

- Prefix shell commands with `rtk`
- Use `uv` for execution
- Use `headroom` if command output, manifest dumps, or logs are large
- Preserve `cavveman` if the calling workflow depends on it

## Canonical Scope

- `data/cached_challenge_fineweb.py`
- `data/download_hf_docs_and_tokenize.py`
- `data/manifest.json`
- `data/tokenizer_specs.json`
- `data/README.md`

## Default Commands

Download a published tokenizer variant:

```bash
rtk uv run python data/cached_challenge_fineweb.py --variant sp1024
```

Download a published tokenizer variant plus the docs cache sidecar:

```bash
rtk uv run python data/cached_challenge_fineweb.py --variant sp1024 --with-docs
```

Re-export shards and tokenizers from the published docs cache:

```bash
rtk uv run python data/download_hf_docs_and_tokenize.py \
  --output-root /tmp/fineweb-export \
  --tokenizer-config ./data/tokenizer_specs.json
```

## Workflow Checklist

- Keep dataset names aligned with the training-script expectations:
  `fineweb10B_<suffix>`.
- Keep shard names aligned with the current export format:
  `fineweb_train_*.bin` and `fineweb_val_*.bin`.
- Keep tokenizer artifact names and manifest entries aligned so
  `train_gpt.py` and `train_gpt_mlx.py` can validate dataset/tokenizer pairing.
- Preserve relative paths in generated manifest payloads unless the task
  explicitly changes the export contract.
- Treat docs-sidecar metadata and manifest stats as load-bearing. Do not invent
  fingerprints, counts, or shard totals.
- If you change tokenizer specs, stay within the built-in supported kinds
  already handled by the script (`pure_byte` / `byte` and SentencePiece BPE)
  unless the task explicitly expands the implementation.

## Verification Guidance

- Prefer lightweight proof such as JSON parsing, targeted smoke runs, and
  script `--help` checks when network or large datasets are unavailable.
- Report network, Hugging Face, or dataset-presence gaps explicitly instead of
  claiming a full export path was tested.
