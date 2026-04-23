#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

if __package__ in (None, ""):
    from log_metrics import (
        LogMetricParseError,
        parse_log_metrics,
        require_exact_roundtrip_metric,
    )
else:
    from scripts.log_metrics import (
        LogMetricParseError,
        parse_log_metrics,
        require_exact_roundtrip_metric,
    )


def calculate_stats(values: list[float]) -> dict[str, float]:
    n = len(values)
    if n < 2:
        # We need at least 2 for std dev / error, but the CLI should probably
        # handle the "one log" case by just reporting the mean if requested,
        # though statistical significance requires more.
        return {
            "n": float(n),
            "mean": float(np.mean(values)),
            "std": 0.0,
            "stderr": 0.0,
            "ci95_low": 0.0,
            "ci95_high": 0.0,
        }

    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1))
    stderr = std / math.sqrt(n)
    
    # 95% Confidence Interval using t-distribution
    t_crit = stats.t.ppf(0.975, df=n - 1)
    ci_half = t_crit * stderr
    
    return {
        "n": float(n),
        "mean": mean,
        "std": std,
        "stderr": stderr,
        "ci95_low": mean - ci_half,
        "ci95_high": mean + ci_half,
    }


def verify_stability(
    log_paths: list[Path],
    sota_bpb: float | None = None,
    required_improvement: float = 0.005,
    max_p_value: float = 0.01,
) -> bool:
    values = []
    labels = set()
    families = set()

    print(f"Parsing {len(log_paths)} logs...")
    try:
        for path in log_paths:
            parsed = parse_log_metrics(path)
            metric = require_exact_roundtrip_metric(parsed)
            values.append(metric.val_bpb)
            labels.add(metric.label)
            families.add(metric.family)
            print(f"  {path}: {metric.val_bpb:.8f} ({metric.label})")

        if len(labels) > 1:
            print(f"❌ Mixed metric labels found: {', '.join(sorted(labels))}")
            print("All logs must use the same exact metric label for stability analysis.")
            return False

        if not values:
            print("❌ No valid metric values extracted.")
            return False

        s = calculate_stats(values)
        label = list(labels)[0]
        family = list(families)[0]

        print("\n--- Summary Statistics ---")
        print(f"Metric: {label} ({family})")
        print(f"Samples: {int(s['n'])}")
        print(f"Mean:    {s['mean']:.8f}")
        if s["n"] >= 2:
            print(f"StdDev:  {s['std']:.8f}")
            print(f"StdErr:  {s['stderr']:.8f}")
            print(f"95% CI:  [{s['ci95_low']:.8f}, {s['ci95_high']:.8f}]")
        else:
            print("StdDev/StdErr/CI: (insufficient samples)")

        if sota_bpb is not None:
            target = sota_bpb - required_improvement
            print("\n--- Significance Test ---")
            print(f"SOTA BPB:             {sota_bpb:.8f}")
            print(f"Required Improvement: {required_improvement:.8f}")
            print(f"Target Threshold:     {target:.8f}")
            
            if s["n"] < 2:
                print("❌ Statistical significance requires at least 2 samples.")
                return False
            
            # One-sided t-test: H0: mean >= target, H1: mean < target
            # (We want to reject H0 to prove improvement)
            t_stat, p_value = stats.ttest_1samp(values, target, alternative="less")
            
            print(f"T-statistic:          {t_stat:.4f}")
            print(f"P-value:              {p_value:.8f}")
            print(f"Max P-value allowed:  {max_p_value:.8f}")

            if p_value < max_p_value:
                print(f"✅ SIGNIFICANT: Mean is significantly below {target:.8f} (p < {max_p_value})")
            else:
                print(f"❌ NOT SIGNIFICANT: p-value {p_value:.8f} >= {max_p_value}")
                return False

    except LogMetricParseError as e:
        print(f"❌ Parse Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify baseline stability and significance across multiple logs."
    )
    parser.add_argument(
        "--logs",
        nargs="+",
        type=Path,
        required=True,
        help="Paths to training log files.",
    )
    parser.add_argument(
        "--sota-bpb",
        type=float,
        help="SOTA BPB to compare against for significance testing.",
    )
    parser.add_argument(
        "--required-improvement",
        type=float,
        default=0.005,
        help="Required absolute improvement over SOTA BPB (default: 0.005).",
    )
    parser.add_argument(
        "--max-p-value",
        type=float,
        default=0.01,
        help="Maximum p-value for significance (default: 0.01).",
    )

    args = parser.parse_args(argv)

    if verify_stability(
        args.logs,
        sota_bpb=args.sota_bpb,
        required_improvement=args.required_improvement,
        max_p_value=args.max_p_value,
    ):
        print("\n🚀 Stability verification PASSED.")
        return 0

    print("\n❌ Stability verification FAILED.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
