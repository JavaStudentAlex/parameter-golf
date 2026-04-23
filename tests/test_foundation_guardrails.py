from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_METRICS = ("val_bpb", "final_int8_zlib_roundtrip", "MAX_WALLCLOCK_SECONDS")
DOCS_WITH_METRICS = ("README.md", "train_gpt.py", "train_gpt_mlx.py")


def test_metric_guardrails_remain_documented() -> None:
    for relative_path in DOCS_WITH_METRICS:
        text = (ROOT / relative_path).read_text()
        for metric in REQUIRED_METRICS:
            assert metric in text, f"{metric} missing from {relative_path}"


def test_project_records_tech_stack_verification() -> None:
    text = (ROOT / "PROJECT.md").read_text()
    for fragment in (
        "## Tech Stack Verification",
        "rtk --version",
        "rtk uv --version",
        "rtk uv run python --version",
        "Python 3.13",
    ):
        assert fragment in text, f"missing {fragment} from PROJECT.md"
