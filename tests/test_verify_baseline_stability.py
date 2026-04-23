import pytest
from pathlib import Path
from scripts.verify_baseline_stability import verify_stability

@pytest.fixture
def tracked_logs():
    base = Path("records/track_10min_16mb/2026-03-19_TrainingOptSeq4096")
    return [
        base / "train.log",
        base / "train_seed1338.log",
        base / "train_seed1339.log",
    ]

def test_verify_stability_tracked_logs(tracked_logs):
    # Verify the baseline logs meet the challenge requirements
    assert verify_stability(
        tracked_logs,
        sota_bpb=1.21613611,
        required_improvement=0.005,
        max_p_value=0.01
    )

def test_verify_stability_no_comparison(tracked_logs):
    # Summary only mode should pass if logs are valid
    assert verify_stability(tracked_logs)

def test_verify_stability_insufficient_samples(tmp_path):
    log = tmp_path / "train.log"
    log.write_text("final_int8_zlib_roundtrip_exact val_loss:2.02857127 val_bpb:1.20143417\n")
    # Comparison should fail if not enough samples for t-test
    assert not verify_stability([log], sota_bpb=1.21613611)

def test_verify_stability_mixed_labels(tmp_path):
    log1 = tmp_path / "train1.log"
    log1.write_text("final_int8_zlib_roundtrip_exact val_loss:2.0 val_bpb:1.2\n")
    log2 = tmp_path / "train2.log"
    log2.write_text("final_int6_roundtrip_exact val_loss:2.1 val_bpb:1.3\n")
    # Mixed labels should fail
    assert not verify_stability([log1, log2])

def test_verify_stability_not_significant(tmp_path):
    # Mean is 1.21, Target is 1.2111 - 0.005 = 1.2061
    # Mean > Target, so it should not be significant
    log1 = tmp_path / "train1.log"
    log1.write_text("final_int8_zlib_roundtrip_exact val_loss:2.0 val_bpb:1.21\n")
    log2 = tmp_path / "train2.log"
    log2.write_text("final_int8_zlib_roundtrip_exact val_loss:2.0 val_bpb:1.21\n")
    assert not verify_stability([log1, log2], sota_bpb=1.2111, required_improvement=0.005)

def test_verify_stability_malformed_input(tmp_path):
    log = tmp_path / "train.log"
    log.write_text("invalid line\n")
    # Should fail if parsing fails
    assert not verify_stability([log])
