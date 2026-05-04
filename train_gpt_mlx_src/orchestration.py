from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pickle
    import time
    import zlib

    import mlx.core as mx
    import mlx.nn as nn
    import numpy as np
    import sentencepiece as spm

    from collections.abc import Callable
    from pathlib import Path

    from data.training_manifest import validate_dataset_tokenizer_pair
    from mlx.utils import tree_flatten, tree_unflatten
    from train_gpt_mlx_src.config import Hyperparameters
    from train_gpt_mlx_src.data import TokenLoader
    from train_gpt_mlx_src.eval import (
        build_sentencepiece_luts,
        eval_val,
        load_validation_tokens,
        loss_and_grad_chunked,
    )
    from train_gpt_mlx_src.model import GPT
    from train_gpt_mlx_src.optimizer import (
        SplitOptimizers,
        accumulate_flat_grads,
        clip_grad_tree,
    )
    from train_gpt_mlx_src.quantization import (
        dequantize_state_dict_int8,
        quantize_state_dict_int8,
    )

# ==============================================================================
# TOKENIZER + VALIDATION METRIC SETUP
# ==============================================================================


def setup_tokenizer_and_validation(
    args: Hyperparameters, log: Callable[[str], None]
) -> tuple[
    spm.SentencePieceProcessor,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    str,
    int,
    int | None,
]:
    if not args.tie_embeddings:
        raise NotImplementedError("train_gpt_mlx.py only supports tied embeddings")
    if not args.tokenizer_path.endswith(".model"):
        raise ValueError(
            f"TOKENIZER_PATH must point to a SentencePiece .model file: {args.tokenizer_path}"
        )
    sp = spm.SentencePieceProcessor(model_file=args.tokenizer_path)
    if int(sp.vocab_size()) != args.vocab_size:
        raise ValueError(
            f"VOCAB_SIZE={args.vocab_size} does not match tokenizer vocab_size={int(sp.vocab_size())}"
        )
    dataset_name, actual_train_files, expected_train_files = (
        validate_dataset_tokenizer_pair(
            args.data_path,
            args.tokenizer_path,
        )
    )
    val_tokens = load_validation_tokens(args.val_files, args.train_seq_len)
    base_bytes_lut, has_leading_space_lut, is_boundary_token_lut = (
        build_sentencepiece_luts(sp, args.vocab_size)
    )
    return (
        sp,
        val_tokens,
        base_bytes_lut,
        has_leading_space_lut,
        is_boundary_token_lut,
        dataset_name,
        actual_train_files,
        expected_train_files,
    )


# ==============================================================================
# MODEL + OPTIMIZER SETUP
# ==============================================================================


def build_model_and_optimizers(args: Hyperparameters) -> tuple[GPT, SplitOptimizers]:
    model = GPT(
        vocab_size=args.vocab_size,
        num_layers=args.num_layers,
        dim=args.model_dim,
        num_heads=args.num_heads,
        num_kv_heads=args.num_kv_heads,
        mlp_mult=args.mlp_mult,
        logit_chunk_tokens=args.logit_chunk_tokens,
        logit_softcap=args.logit_softcap,
        rope_base=args.rope_base,
        tied_embed_init_std=args.tied_embed_init_std,
        qk_gain_init=args.qk_gain_init,
    )
    opt = SplitOptimizers(model, args)
    return model, opt


# ==============================================================================
# RUN CONFIG LOGGING
# ==============================================================================


def log_run_config(
    args: Hyperparameters,
    model: GPT,
    opt: SplitOptimizers,
    val_tokens: np.ndarray,
    dataset_name: str,
    actual_train_files: int,
    expected_train_files: int | None,
    log: Callable[[str], None],
) -> None:
    n_params = sum(int(np.prod(p.shape)) for _, p in tree_flatten(model.parameters()))
    log(f"run_id:{args.run_id}")
    log(f"mlx_version:{mx.__version__}")
    log(f"train_loader:shards pattern={args.train_files}")
    log(f"val_loader:shards pattern={args.val_files} tokens:{val_tokens.size - 1}")
    if expected_train_files is None:
        log(f"train_loader:dataset:{dataset_name} train_shards:{actual_train_files}")
    elif actual_train_files < expected_train_files:
        log(
            f"WARNING: train_loader:subset dataset:{dataset_name} "
            f"train_shards:{actual_train_files}/{expected_train_files} "
            f"new epochs will arrive sooner than the full dataset"
        )
    else:
        log(
            f"train_loader:dataset:{dataset_name} train_shards:{actual_train_files}/{expected_train_files}"
        )
    log(f"tokenizer_path:{args.tokenizer_path}")
    log(
        f"model_params:{n_params} vocab_size:{args.vocab_size} layers:{args.num_layers} "
        f"dim:{args.model_dim} heads:{args.num_heads} kv_heads:{args.num_kv_heads} "
        f"seq_len:{args.train_seq_len} tie_embeddings:{args.tie_embeddings}"
    )
    log(
        f"iterations:{args.iterations} train_batch_tokens:{args.train_batch_tokens} grad_accum_steps:{args.grad_accum_steps} "
        f"microbatch_tokens:{args.microbatch_tokens} microbatch_batch_size:{args.microbatch_tokens // args.train_seq_len} "
        f"val_batch_size:{args.val_batch_size} "
        f"warmup_steps:{args.warmup_steps} max_wallclock_seconds:{args.max_wallclock_seconds:.3f}"
    )
    log(f"mlx_max_microbatch_tokens:{args.mlx_max_microbatch_tokens}")
    log(
        f"optimizer:muon+adam muon_matrix_params:{len(opt.matrix_keys)} scalar_params:{len(opt.scalar_keys)} "
        f"embed_lr:{args.tied_embed_lr} "
        f"matrix_lr:{args.matrix_lr} scalar_lr:{args.scalar_lr} "
        f"muon_momentum:{args.muon_momentum} muon_steps:{args.muon_backend_steps}"
    )
    log(
        f"val_bpb:enabled tokenizer_kind=sentencepiece tokenizer_path={args.tokenizer_path}"
    )
    log(f"compute_dtype:{COMPUTE_DTYPE} compile:True")
    log(
        f"dtypes tok_emb:{model.tok_emb.weight.dtype} "
        f"linear_weight:{model.blocks[0].attn.c_q.weight.dtype} "
        f"skip_weights:{model.skip_weights.dtype}"
    )


# ==============================================================================
# TRAINING WARMUP
# ==============================================================================


def run_warmup(
    args: Hyperparameters,
    model: GPT,
    train_loader: TokenLoader,
    compiled_loss: Callable[[mx.array, mx.array], mx.array],
    compiled_loss_and_grad: Callable[[mx.array, mx.array], tuple[mx.array, dict[str, mx.array]]],
    val_tokens: np.ndarray,
    dataset_name: str,
    log: Callable[[str], None],
) -> TokenLoader:
    if args.warmup_steps <= 0:
        return train_loader
    for warmup_step in range(args.warmup_steps):
        accum: dict[str, mx.array] | None = None
        warmup_loss = mx.array(0.0, dtype=mx.float32)
        grad_scale = 1.0 / args.grad_accum_steps
        for _ in range(args.grad_accum_steps):
            warmup_loss, grads = loss_and_grad_chunked(
                args, train_loader, compiled_loss_and_grad
            )
            accum = accumulate_flat_grads(accum, grads, grad_scale)
        mx.eval(warmup_loss, accum)
        mx.synchronize()
        if (
            args.warmup_steps <= 20
            or (warmup_step + 1) % 10 == 0
            or warmup_step + 1 == args.warmup_steps
        ):
            log(f"warmup_step:{warmup_step + 1}/{args.warmup_steps}")

    val_batch_tokens = args.val_batch_size // args.grad_accum_steps
    if val_batch_tokens < args.train_seq_len:
        raise ValueError(
            "VAL_BATCH_SIZE must provide at least one sequence; "
            f"got VAL_BATCH_SIZE={args.val_batch_size}, GRAD_ACCUM_STEPS={args.grad_accum_steps}, "
            f"TRAIN_SEQ_LEN={args.train_seq_len}"
        )
    warm_val_seqs = min(
        val_batch_tokens // args.train_seq_len,
        (val_tokens.size - 1) // args.train_seq_len,
    )
    warm_chunk = val_tokens[: warm_val_seqs * args.train_seq_len + 1]
    x_val = mx.array(warm_chunk[:-1].reshape(-1, args.train_seq_len), dtype=mx.int32)
    y_val = mx.array(warm_chunk[1:].reshape(-1, args.train_seq_len), dtype=mx.int32)
    warm_val_loss = compiled_loss(x_val, y_val)
    mx.eval(warm_val_loss)
    mx.synchronize()

    return TokenLoader(args.train_files, log_fn=log, dataset_name=dataset_name)


# ==============================================================================
# TRAINING LOOP
# ==============================================================================


def run_training_loop(
    args: Hyperparameters,
    model: GPT,
    opt: SplitOptimizers,
    train_loader: TokenLoader,
    val_tokens: np.ndarray,
    luts: tuple[np.ndarray, np.ndarray, np.ndarray],
    compiled_loss: Callable[[mx.array, mx.array], mx.array],
    compiled_loss_and_grad: Callable[[mx.array, mx.array], tuple[mx.array, dict[str, mx.array]]],
    log: Callable[[str], None],
) -> None:
    base_bytes_lut, has_leading_space_lut, is_boundary_token_lut = luts
    train_time_ms = 0.0
    max_wallclock_ms = (
        1000.0 * args.max_wallclock_seconds if args.max_wallclock_seconds > 0 else None
    )
    stop_after_step: int | None = None
    t0 = time.perf_counter()
    step = 0
    while True:
        last_step = step == args.iterations or (
            stop_after_step is not None and step >= stop_after_step
        )
        if last_step or (args.val_loss_every > 0 and step % args.val_loss_every == 0):
            train_time_ms += 1000.0 * (time.perf_counter() - t0)
            val_loss, val_bpb = eval_val(
                args,
                compiled_loss,
                val_tokens,
                base_bytes_lut,
                has_leading_space_lut,
                is_boundary_token_lut,
                log_fn=log,
            )
            if step % 25 == 0 or last_step:
                log(
                    f"step:{step}/{args.iterations} val_loss:{val_loss:.4f} val_bpb:{val_bpb:.4f} "
                    f"train_time:{train_time_ms:.0f}ms step_avg:{train_time_ms / max(step, 1):.2f}ms"
                )
            t0 = time.perf_counter()
        if last_step:
            if stop_after_step is not None and step < args.iterations:
                log(
                    f"stopping_early: wallclock_cap train_time:{train_time_ms:.0f}ms step:{step}/{args.iterations}"
                )
            break

        lr_mul = args.lr_mul(step, train_time_ms + 1000.0 * (time.perf_counter() - t0))
        step_t0 = time.perf_counter()

        accum: dict[str, mx.array] | None = None
        train_loss = mx.array(0.0, dtype=mx.float32)
        grad_scale = 1.0 / args.grad_accum_steps
        for _ in range(args.grad_accum_steps):
            loss, grads = loss_and_grad_chunked(
                args, train_loader, compiled_loss_and_grad
            )
            accum = accumulate_flat_grads(accum, grads, grad_scale)
            train_loss = train_loss + loss.astype(mx.float32) * grad_scale
            if args.mlx_eager_eval:
                mx.eval(
                    train_loss, accum
                )  # materialize each microbatch to cap peak memory

        grads = tree_unflatten(list(accum.items()))
        grads = clip_grad_tree(grads, args.grad_clip_norm)
        train_loss_value = float(train_loss.item())
        opt.step(model, grads, step=step, lr_mul=lr_mul)
        mx.synchronize()

        step_ms = 1000.0 * (time.perf_counter() - step_t0)
        approx_train_time_ms = train_time_ms + 1000.0 * (time.perf_counter() - t0)
        tok_s = args.train_batch_tokens / (step_ms / 1000.0)
        step += 1
        if args.train_log_every > 0 and (
            step <= 10
            or step % args.train_log_every == 0
            or stop_after_step is not None
        ):
            log(
                f"step:{step}/{args.iterations} train_loss:{train_loss_value:.4f} "
                f"train_time:{approx_train_time_ms:.0f}ms step_avg:{approx_train_time_ms / step:.2f}ms tok_s:{tok_s:.0f}"
            )
        if (
            max_wallclock_ms is not None
            and stop_after_step is None
            and approx_train_time_ms >= max_wallclock_ms
        ):
            stop_after_step = step


# ==============================================================================
# FINAL SERIALIZATION + QUANTIZED ROUNDTRIP EVAL
# ==============================================================================


def finalize_and_validate_roundtrip(
    args: Hyperparameters,
    model: GPT,
    val_tokens: np.ndarray,
    luts: tuple[np.ndarray, np.ndarray, np.ndarray],
    compiled_loss: Callable[[mx.array, mx.array], mx.array],
    code: str,
    log: Callable[[str], None],
) -> None:
    base_bytes_lut, has_leading_space_lut, is_boundary_token_lut = luts
    out_dir = Path(args.out_dir)
    out_path = out_dir / f"{args.run_id}_mlx_model.npz"
    flat_state = {k: v for k, v in tree_flatten(model.state)}
    mx.savez(str(out_path), **flat_state)
    log(f"saved_model:{out_path} bytes:{out_path.stat().st_size}")

    quant_obj, quant_stats = quantize_state_dict_int8(flat_state)
    quant_raw = pickle.dumps(quant_obj, protocol=pickle.HIGHEST_PROTOCOL)
    quant_blob = zlib.compress(quant_raw, level=9)
    quant_serialized_bytes = len(quant_raw)
    quant_path = out_dir / f"{args.run_id}_mlx_model.int8.ptz"
    with quant_path.open("wb") as f:
        f.write(quant_blob)
    quant_file_bytes = quant_path.stat().st_size
    code_bytes = len(code.encode("utf-8"))
    ratio = quant_stats["baseline_tensor_bytes"] / max(
        quant_stats["int8_payload_bytes"], 1
    )
    log(
        f"serialized_model_int8_zlib:{quant_file_bytes} bytes "
        f"(payload:{quant_stats['int8_payload_bytes']} raw_pickle:{quant_serialized_bytes} payload_ratio:{ratio:.2f}x)"
    )
    log(f"Code size: {code_bytes} bytes")
    log(f"Total submission size int8+zlib: {quant_file_bytes + code_bytes} bytes")

    with quant_path.open("rb") as f:
        quant_blob_disk = f.read()
    quant_flat = dequantize_state_dict_int8(
        pickle.loads(zlib.decompress(quant_blob_disk))
    )
    model.update(tree_unflatten(list(quant_flat.items())))
    q_t0 = time.perf_counter()
    q_val_loss, q_val_bpb = eval_val(
        args,
        compiled_loss,
        val_tokens,
        base_bytes_lut,
        has_leading_space_lut,
        is_boundary_token_lut,
        log_fn=log,
    )
    q_eval_ms = 1000.0 * (time.perf_counter() - q_t0)
    log(
        f"final_int8_zlib_roundtrip val_loss:{q_val_loss:.4f} val_bpb:{q_val_bpb:.4f} eval_time:{q_eval_ms:.0f}ms"
    )
    log(
        f"final_int8_zlib_roundtrip_exact val_loss:{q_val_loss:.8f} val_bpb:{q_val_bpb:.8f}"
    )
