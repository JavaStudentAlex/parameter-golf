from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.log_metrics import LogMetricParseError, parse_log_metrics
from scripts.verify_baseline_log import verify_log

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_baseline_log.py"
NAIVE_BASELINE_LOG = (
    ROOT / "records" / "track_10min_16mb" / "2026-03-17_NaiveBaseline" / "train.log"
)
SMEARGATE_INT6_LOG = (
    ROOT
    / "records"
    / "track_10min_16mb"
    / "2026-03-19_smeargate_orthoinit_muonwd"
    / "train.log"
)


def test_parse_log_metrics_reads_historical_int8_record() -> None:
    parsed_log = parse_log_metrics(NAIVE_BASELINE_LOG)

    assert parsed_log.exact_metric_labels == ("final_int8_zlib_roundtrip_exact",)
    assert parsed_log.preferred_exact_metric().family == "int8+zlib"
    assert parsed_log.preferred_exact_metric().val_bpb == pytest.approx(1.22436570)
    assert parsed_log.submission_size is not None
    assert parsed_log.submission_size.variant == "int8+zlib"
    assert parsed_log.submission_size.total_bytes == 15_863_489
    assert parsed_log.wallclock_cap is not None
    assert parsed_log.wallclock_cap.train_time_ms == 600_038


def test_parse_log_metrics_reads_historical_int6_record() -> None:
    parsed_log = parse_log_metrics(SMEARGATE_INT6_LOG)

    assert parsed_log.exact_metric_labels == ("final_int6_roundtrip_exact",)
    assert parsed_log.preferred_exact_metric().family == "int6"
    assert parsed_log.preferred_exact_metric().val_bpb == pytest.approx(1.18908459)
    assert parsed_log.submission_size is not None
    assert parsed_log.submission_size.variant == "int6+zstd-22"
    assert parsed_log.submission_size.total_bytes == 15_878_809
    assert parsed_log.wallclock_cap is not None
    assert parsed_log.wallclock_cap.train_time_ms == 599_974


def test_parse_log_metrics_keeps_metric_metadata_for_mixed_exact_labels(
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "mixed_metrics.log"
    log_file.write_text(
        "stopping_early: wallclock_cap train_time:600038ms step:13780/20000\n"
        "Total submission size int8+zlib: 15863489 bytes\n"
        "final_int6_roundtrip_exact val_loss:2.00771951 val_bpb:1.18908459\n"
        "final_int8_zlib_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n",
        encoding="utf-8",
    )

    parsed_log = parse_log_metrics(log_file)

    assert parsed_log.exact_metric_labels == (
        "final_int6_roundtrip_exact",
        "final_int8_zlib_roundtrip_exact",
    )
    assert parsed_log.preferred_exact_metric().label == "final_int8_zlib_roundtrip_exact"


@pytest.mark.parametrize(
    "log_path",
    [
        NAIVE_BASELINE_LOG,
        SMEARGATE_INT6_LOG,
    ],
)
def test_verify_log_passes_historical_records(log_path: Path) -> None:
    assert verify_log(log_path, require_wallclock_cap=True) is True


def test_verify_log_fails_missing_roundtrip(tmp_path: Path) -> None:
    log_file = tmp_path / "missing_roundtrip.log"
    log_file.write_text(
        "stopping_early: wallclock_cap train_time:600038ms step:13780/20000\n"
        "Total submission size int8+zlib: 15863489 bytes\n",
        encoding="utf-8",
    )

    assert verify_log(log_file) is False


def test_verify_log_fails_oversize_when_compressed_size_is_present(tmp_path: Path) -> None:
    log_file = tmp_path / "oversize.log"
    log_file.write_text(
        "Total submission size: 5000000 bytes\n"
        "Total submission size int8+zlib: 17000000 bytes\n"
        "final_int8_zlib_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n",
        encoding="utf-8",
    )

    assert verify_log(log_file) is False


def test_parse_log_metrics_rejects_non_integer_size_bytes(tmp_path: Path) -> None:
    log_file = tmp_path / "bad_size.log"
    log_file.write_text(
        "Total submission size int6+zstd: not-a-number bytes\n"
        "final_int6_roundtrip_exact val_loss:2.00771951 val_bpb:1.18908459\n",
        encoding="utf-8",
    )

    with pytest.raises(LogMetricParseError, match="malformed total submission size proof"):
        parse_log_metrics(log_file)


def test_parse_log_metrics_rejects_truncated_wallclock_line(tmp_path: Path) -> None:
    log_file = tmp_path / "bad_wallclock.log"
    log_file.write_text(
        "stopping_early: wallclock_cap train_time:600038ms step:\n"
        "Total submission size int8+zlib: 15863489 bytes\n"
        "final_int8_zlib_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n",
        encoding="utf-8",
    )

    with pytest.raises(LogMetricParseError, match="malformed wallclock-cap proof"):
        parse_log_metrics(log_file)


def test_parse_log_metrics_rejects_unsupported_exact_metric_label(tmp_path: Path) -> None:
    log_file = tmp_path / "unsupported_metric.log"
    log_file.write_text(
        "Total submission size int8+zlib: 15863489 bytes\n"
        "final_quantized_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n",
        encoding="utf-8",
    )

    with pytest.raises(LogMetricParseError, match="unsupported exact metric label"):
        parse_log_metrics(log_file)


def test_verify_log_fails_missing_file(tmp_path: Path) -> None:
    missing_log = tmp_path / "missing.log"
    assert verify_log(missing_log) is False


@pytest.mark.parametrize(
    "argv",
    [
        [str(NAIVE_BASELINE_LOG), "--require-wallclock-cap"],
        ["--log", str(NAIVE_BASELINE_LOG), "--require-wallclock-cap"],
    ],
)
def test_cli_accepts_positional_and_flag_log_paths(argv: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASSED" in result.stdout
