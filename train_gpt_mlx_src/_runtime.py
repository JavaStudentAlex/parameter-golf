# Shared quantization patterns are assembled from train_gpt_mlx_src/quantization.py before this runtime fragment.
# Optimizer helpers are assembled from train_gpt_mlx_src/optimizer.py before this runtime fragment.
# Training orchestration helpers are assembled from train_gpt_mlx_src/orchestration.py before this runtime fragment.

# ==============================================================================
# TRAINING
# ==============================================================================

def main() -> None:
    args = Hyperparameters()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    logfile = out_dir / f"{args.run_id}.txt"
    print(logfile)

    def log(msg: str, console: bool = True) -> None:
        if console:
            print(msg)
        with logfile.open("a", encoding="utf-8") as f:
            print(msg, file=f)

    code = Path(__file__).read_text(encoding="utf-8")
    log(code, console=False)
    log("=" * 100, console=False)
    log(f"Running Python {sys.version}", console=False)
    log(f"Running MLX {mx.__version__}", console=False)
    log("=" * 100, console=False)

    sp, val_tokens, base_bytes_lut, has_leading_space_lut, is_boundary_token_lut, dataset_name, actual_train_files, expected_train_files = (
        setup_tokenizer_and_validation(args, log)
    )
    luts = (base_bytes_lut, has_leading_space_lut, is_boundary_token_lut)

    mx.random.seed(args.seed)
    train_loader = TokenLoader(args.train_files, log_fn=log, dataset_name=dataset_name)

    model, opt = build_model_and_optimizers(args)

    compiled_loss = mx.compile(
        lambda x, y: model.loss(x, y), inputs=model.state, outputs=model.state
    )
    compiled_loss_and_grad = mx.compile(
        nn.value_and_grad(model, lambda x, y: model.loss(x, y)),
        inputs=model.state,
        outputs=model.state,
    )

    log_run_config(args, model, opt, val_tokens, dataset_name, actual_train_files, expected_train_files, log)

    train_loader = run_warmup(
        args, model, train_loader, compiled_loss, compiled_loss_and_grad,
        val_tokens, dataset_name, log,
    )

    run_training_loop(
        args, model, opt, train_loader, val_tokens, luts,
        compiled_loss, compiled_loss_and_grad, log,
    )

    finalize_and_validate_roundtrip(args, model, val_tokens, luts, compiled_loss, code, log)


if __name__ == "__main__":
    main()
