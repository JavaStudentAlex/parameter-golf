import pytest
from pathlib import Path
from scripts.verify_baseline_log import verify_log

def test_verify_log_passes_valid_log(tmp_path):
    log_file = tmp_path / "valid.log"
    log_file.write_text(
        "stopping_early: wallclock_cap train_time:600038ms step:13780/20000\n"
        "Total submission size int8+zlib: 15863489 bytes\n"
        "final_int8_zlib_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n"
    )
    assert verify_log(log_file, require_wallclock_cap=True) is True

def test_verify_log_fails_missing_roundtrip(tmp_path):
    log_file = tmp_path / "missing_roundtrip.log"
    log_file.write_text(
        "stopping_early: wallclock_cap train_time:600038ms step:13780/20000\n"
        "Total submission size int8+zlib: 15863489 bytes\n"
    )
    assert verify_log(log_file) is False

def test_verify_log_fails_oversize(tmp_path):
    log_file = tmp_path / "oversize.log"
    log_file.write_text(
        "Total submission size int8+zlib: 17000000 bytes\n"
        "final_int8_zlib_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n"
    )
    assert verify_log(log_file) is False

def test_verify_log_fails_missing_wallclock_cap_when_required(tmp_path):
    log_file = tmp_path / "missing_wallclock.log"
    log_file.write_text(
        "Total submission size int8+zlib: 15863489 bytes\n"
        "final_int8_zlib_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n"
    )
    assert verify_log(log_file, require_wallclock_cap=True) is False

def test_verify_log_passes_without_wallclock_cap_when_not_required(tmp_path):
    log_file = tmp_path / "smoke.log"
    log_file.write_text(
        "Total submission size int8+zlib: 15863489 bytes\n"
        "final_int8_zlib_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n"
    )
    assert verify_log(log_file, require_wallclock_cap=False) is True

def test_verify_log_handles_plain_submission_size(tmp_path):
    log_file = tmp_path / "plain_size.log"
    log_file.write_text(
        "Total submission size: 5000000 bytes\n"
        "final_int8_zlib_roundtrip_exact val_loss:2.07269931 val_bpb:1.22436570\n"
    )
    assert verify_log(log_file) is True
