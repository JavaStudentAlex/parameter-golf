# Parameter Golf Project

## Overview

Parameter Golf is an OpenAI Model Craft Challenge repository for training the best language model that fits in a 16MB artifact and trains in under 10 minutes on 8xH100s. This repo keeps the challenge narrative, the canonical requirement register, the baseline training entry points, and the data/export helpers together so contributors can iterate without losing sight of the rules.

## Challenge Constraints

The canonical requirement register is the source of truth for these constraints. This section is a quick orientation, not a replacement for the register.

- **R001** — Submission artifacts must fit within a 16MB decimal (16,000,000 bytes) limit. The artifact is code bytes plus compressed model bytes, and no external downloads, training dataset access, or network calls are allowed during evaluation.
- **R002** — Training must complete in under 10 minutes on 8xH100s. The same wallclock cap applies during evaluation.
- **R003** — Submissions must provide enough run logs to show *p* < 0.01 for a 0.005-nat improvement over SOTA. This requirement is waived for submissions that improve speed through systems optimization without changing the ML.

## Tech Stack

- **Runtime:** Python 3.13.
- **Training:** PyTorch and `torch.distributed` for the CUDA path, plus MLX for the Apple Silicon path.
- **Data and tokenization:** sentencepiece, tiktoken, datasets, huggingface-hub, and NumPy.
- **Tooling:** `uv` is the dependency manager, and `rtk` is the required CLI proxy for repository commands.
- **Entry points:** the repository keeps separate baseline training flows for CUDA and Apple Silicon so the challenge can be exercised on both local and remote hardware.

## Data Pipeline

The data workflow centers on cached FineWeb exports, tokenizer artifacts, manifests, and selected-document caches.

- The cached FineWeb downloader fetches a published tokenizer variant and can limit itself to a prefix of train shards from a frozen export.
- Validation always uses the fixed `fineweb_val_*` split, so training order stays aligned with the baseline for that tokenizer family.
- The docs retokenizer can rebuild tokenizer and shard exports from the same selected-document set, and the source-manifest sidecar records `docs_sha256` so rebuilds can be verified against the exact document list and order.
- CPU-heavy exports expose tuning knobs for batch size and tokenizer worker counts, including batched encoding, tokenizer threads, tiktoken threads, and GPT-2 decode batching.

Use the data workflow guide for the exact commands and environment knobs when you need to download, rebuild, or tune exports.

## Tech Stack Verification

Verified with the repo's required `rtk` proxy and uv-managed Python environment:

| Check | Result |
| --- | --- |
| `rtk --version` | `rtk 0.37.2` |
| `rtk uv --version` | `uv 0.11.6 (x86_64-unknown-linux-gnu)` |
| `rtk uv run python --version` | `Python 3.13.12` |

Metric guardrails confirmed via grep:

- `train_gpt.py` contains `val_bpb`, `final_int8_zlib_roundtrip`, and `MAX_WALLCLOCK_SECONDS`.
- `train_gpt_mlx.py` contains `val_bpb`, `final_int8_zlib_roundtrip`, and `MAX_WALLCLOCK_SECONDS`.
- `README.md` references `val_bpb`, `final_int8_zlib_roundtrip`, and `MAX_WALLCLOCK_SECONDS`.
