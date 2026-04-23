from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXACT_METRIC_FAMILIES = {
    "final_int8_zlib_roundtrip_exact": "int8+zlib",
    "final_int6_roundtrip_exact": "int6",
}
EXACT_METRIC_PREFERENCE = (
    "final_int8_zlib_roundtrip_exact",
    "final_int6_roundtrip_exact",
)

EXACT_METRIC_LINE_RE = re.compile(
    r"^(?P<label>final_[a-z0-9_]+_roundtrip_exact)\s+"
    r"val_loss:(?P<val_loss>\d+(?:\.\d+)?)\s+"
    r"val_bpb:(?P<val_bpb>\d+(?:\.\d+)?)\s*$"
)
SUBMISSION_SIZE_LINE_RE = re.compile(
    r"^Total submission size(?: (?P<variant>[^:]+))?:\s*(?P<total_bytes>\d+)\s+bytes\s*$"
)
WALLCLOCK_CAP_LINE_RE = re.compile(
    r"^stopping_early: wallclock_cap\s+"
    r"train_time:\s*(?P<train_time_ms>\d+)ms\s+"
    r"step:\s*(?P<step>\d+)\/(?P<total_steps>\d+)\s*$"
)


class LogMetricParseError(ValueError):
    """Raised when a tracked proof surface is missing or malformed."""


@dataclass(frozen=True)
class ExactMetricProof:
    label: str
    family: str
    val_loss: float
    val_bpb: float
    line_number: int


@dataclass(frozen=True)
class SubmissionSizeProof:
    label: str
    variant: str
    total_bytes: int
    line_number: int
    is_compressed: bool


@dataclass(frozen=True)
class WallclockCapProof:
    train_time_ms: int
    step: int
    total_steps: int
    line_number: int


@dataclass(frozen=True)
class ParsedLogMetrics:
    path: Path
    exact_metrics: tuple[ExactMetricProof, ...]
    submission_size: SubmissionSizeProof | None
    wallclock_cap: WallclockCapProof | None

    @property
    def exact_metric_labels(self) -> tuple[str, ...]:
        return tuple(metric.label for metric in self.exact_metrics)

    def preferred_exact_metric(self) -> ExactMetricProof:
        for preferred_label in EXACT_METRIC_PREFERENCE:
            for metric in self.exact_metrics:
                if metric.label == preferred_label:
                    return metric
        if self.exact_metrics:
            return self.exact_metrics[-1]

        supported_labels = ", ".join(EXACT_METRIC_PREFERENCE)
        raise LogMetricParseError(
            f"{self.path}: missing exact roundtrip proof line "
            f"(supported labels: {supported_labels})."
        )


def _malformed_log_line(log_path: Path, line_number: int, surface: str, line: str) -> LogMetricParseError:
    return LogMetricParseError(
        f"{log_path}:{line_number}: malformed {surface} line: {line!r}"
    )


def _parse_exact_metric_line(log_path: Path, line_number: int, line: str) -> ExactMetricProof:
    match = EXACT_METRIC_LINE_RE.fullmatch(line)
    if not match:
        raise _malformed_log_line(log_path, line_number, "exact roundtrip proof", line)

    label = match.group("label")
    family = SUPPORTED_EXACT_METRIC_FAMILIES.get(label)
    if family is None:
        supported_labels = ", ".join(EXACT_METRIC_PREFERENCE)
        raise LogMetricParseError(
            f"{log_path}:{line_number}: unsupported exact metric label "
            f"{label!r} (supported labels: {supported_labels})."
        )

    return ExactMetricProof(
        label=label,
        family=family,
        val_loss=float(match.group("val_loss")),
        val_bpb=float(match.group("val_bpb")),
        line_number=line_number,
    )


def _parse_submission_size_line(log_path: Path, line_number: int, line: str) -> SubmissionSizeProof:
    match = SUBMISSION_SIZE_LINE_RE.fullmatch(line)
    if not match:
        raise _malformed_log_line(log_path, line_number, "total submission size proof", line)

    variant = match.group("variant") or "plain"
    label = "Total submission size" if variant == "plain" else f"Total submission size {variant}"
    return SubmissionSizeProof(
        label=label,
        variant=variant,
        total_bytes=int(match.group("total_bytes")),
        line_number=line_number,
        is_compressed=variant != "plain",
    )


def _parse_wallclock_cap_line(log_path: Path, line_number: int, line: str) -> WallclockCapProof:
    match = WALLCLOCK_CAP_LINE_RE.fullmatch(line)
    if not match:
        raise _malformed_log_line(log_path, line_number, "wallclock-cap proof", line)

    return WallclockCapProof(
        train_time_ms=int(match.group("train_time_ms")),
        step=int(match.group("step")),
        total_steps=int(match.group("total_steps")),
        line_number=line_number,
    )


def parse_log_metrics(log_path: Path) -> ParsedLogMetrics:
    if not log_path.exists():
        raise LogMetricParseError(f"log file not found at {log_path}")

    content = log_path.read_text(encoding="utf-8")

    exact_metrics_by_label: dict[str, ExactMetricProof] = {}
    compressed_submission_size: SubmissionSizeProof | None = None
    plain_submission_size: SubmissionSizeProof | None = None
    wallclock_cap: WallclockCapProof | None = None

    for line_number, line in enumerate(content.splitlines(), start=1):
        if line.startswith("final_") and "_roundtrip_exact" in line:
            metric = _parse_exact_metric_line(log_path, line_number, line)
            exact_metrics_by_label[metric.label] = metric
            continue

        if line.startswith("Total submission size"):
            submission_size = _parse_submission_size_line(log_path, line_number, line)
            if submission_size.is_compressed:
                compressed_submission_size = submission_size
            else:
                plain_submission_size = submission_size
            continue

        if line.startswith("stopping_early: wallclock_cap"):
            wallclock_cap = _parse_wallclock_cap_line(log_path, line_number, line)

    exact_metrics = tuple(
        sorted(exact_metrics_by_label.values(), key=lambda metric: metric.line_number)
    )
    submission_size = compressed_submission_size or plain_submission_size
    return ParsedLogMetrics(
        path=log_path,
        exact_metrics=exact_metrics,
        submission_size=submission_size,
        wallclock_cap=wallclock_cap,
    )


def require_exact_roundtrip_metric(parsed_log: ParsedLogMetrics) -> ExactMetricProof:
    return parsed_log.preferred_exact_metric()


def require_submission_size_proof(parsed_log: ParsedLogMetrics) -> SubmissionSizeProof:
    if parsed_log.submission_size is None:
        raise LogMetricParseError(
            f"{parsed_log.path}: missing total submission size proof line."
        )
    return parsed_log.submission_size


def require_wallclock_cap_proof(parsed_log: ParsedLogMetrics) -> WallclockCapProof:
    if parsed_log.wallclock_cap is None:
        raise LogMetricParseError(
            f"{parsed_log.path}: missing 'stopping_early: wallclock_cap' line."
        )
    return parsed_log.wallclock_cap
