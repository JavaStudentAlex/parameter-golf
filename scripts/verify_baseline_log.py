#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    from log_metrics import (
        LogMetricParseError,
        parse_log_metrics,
        require_exact_roundtrip_metric,
        require_submission_size_proof,
        require_wallclock_cap_proof,
    )
else:
    from scripts.log_metrics import (
        LogMetricParseError,
        parse_log_metrics,
        require_exact_roundtrip_metric,
        require_submission_size_proof,
        require_wallclock_cap_proof,
    )

DEFAULT_MAX_TOTAL_BYTES = 16_000_000


def verify_log(
    log_path: Path,
    require_wallclock_cap: bool = False,
    *,
    require_roundtrip_exact: bool = True,
    require_total_size: bool = True,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
) -> bool:
    try:
        parsed_log = parse_log_metrics(log_path)

        if require_roundtrip_exact:
            metric = require_exact_roundtrip_metric(parsed_log)
            print(
                "✅ Found exact roundtrip metric: "
                f"{metric.label} val_loss={metric.val_loss:.8f}, val_bpb={metric.val_bpb:.8f}"
            )

        if require_total_size:
            submission_size = require_submission_size_proof(parsed_log)
            if submission_size.total_bytes > max_total_bytes:
                print(
                    f"❌ {submission_size.label}: {submission_size.total_bytes} bytes "
                    f"exceeds limit of {max_total_bytes} bytes."
                )
                return False
            print(
                f"✅ {submission_size.label}: {submission_size.total_bytes} bytes "
                f"(within {max_total_bytes} byte limit)"
            )

        if require_wallclock_cap:
            wallclock_cap = require_wallclock_cap_proof(parsed_log)
            print(
                "✅ Found wallclock-cap proof: "
                f"train_time={wallclock_cap.train_time_ms}ms "
                f"step={wallclock_cap.step}/{wallclock_cap.total_steps}"
            )
    except LogMetricParseError as error:
        print(f"Error: {error}")
        return False

    return True


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify training log for challenge compliance.")
    parser.add_argument("log_file", nargs="?", type=Path, help="Path to the training log file.")
    parser.add_argument("--log", dest="log_path", type=Path, help="Path to the training log file.")
    parser.add_argument(
        "--require-roundtrip-exact",
        dest="require_roundtrip_exact",
        action="store_true",
        default=True,
        help="Require the exact roundtrip metric line.",
    )
    parser.add_argument(
        "--require-total-size",
        dest="require_total_size",
        action="store_true",
        default=True,
        help="Require a total submission size line.",
    )
    parser.add_argument(
        "--require-wallclock-cap",
        action="store_true",
        help="Require proof of wallclock cap early stop.",
    )
    parser.add_argument(
        "--max-total-bytes",
        type=int,
        default=DEFAULT_MAX_TOTAL_BYTES,
        help="Maximum allowed total submission size in bytes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    log_path = args.log_path or args.log_file
    if log_path is None:
        parser.error("a training log path must be provided either positionally or via --log")
    if args.log_path is not None and args.log_file is not None and args.log_path != args.log_file:
        parser.error(
            "provide the training log path either positionally or via --log, not both with different values"
        )

    if verify_log(
        log_path,
        require_wallclock_cap=args.require_wallclock_cap,
        require_roundtrip_exact=args.require_roundtrip_exact,
        require_total_size=args.require_total_size,
        max_total_bytes=args.max_total_bytes,
    ):
        print("🚀 Log verification PASSED.")
        return 0

    print("❌ Log verification FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
