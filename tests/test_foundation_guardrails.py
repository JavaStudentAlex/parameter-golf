from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_METRICS = ("val_bpb", "final_int8_zlib_roundtrip", "MAX_WALLCLOCK_SECONDS")
DOCS_WITH_METRICS = ("README.md", "train_gpt.py", "train_gpt_mlx.py")
REPO_COMMANDS = (
    "rtk uv sync",
    "rtk uv run python",
    "rtk uv run torchrun",
    "scripts/verify_baseline_log.py",
    "scripts/verify_baseline_stability.py",
)
STABILITY_CONSTANTS = ("0.005", "p < 0.01")


def test_metric_guardrails_remain_documented() -> None:
    for relative_path in DOCS_WITH_METRICS:
        text = (ROOT / relative_path).read_text()
        for metric in REQUIRED_METRICS:
            assert metric in text, f"{metric} missing from {relative_path}"


def test_repo_compliant_commands_documented() -> None:
    text = (ROOT / "README.md").read_text()
    for cmd in REPO_COMMANDS:
        assert cmd in text, f"README.md missing repo-compliant command pattern: {cmd}"


def test_stability_requirements_documented() -> None:
    text = (ROOT / "README.md").read_text()
    for constant in STABILITY_CONSTANTS:
        assert constant in text, f"README.md missing stability constant: {constant}"


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
