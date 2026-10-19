from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class Sample:
    """Request counters for one completed observation bucket."""

    timestamp: datetime
    total: int
    errors: int

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("sample timestamps must include a timezone")
        if self.total < 0 or self.errors < 0:
            raise ValueError("request counters cannot be negative")
        if self.errors > self.total:
            raise ValueError("errors cannot exceed total requests")


@dataclass(frozen=True)
class AlertPolicy:
    name: str
    long_window: timedelta
    short_window: timedelta
    threshold: float
    severity: str

    def __post_init__(self) -> None:
        if self.short_window <= timedelta(0) or self.long_window <= timedelta(0):
            raise ValueError("alert windows must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be smaller than long_window")
        if self.threshold <= 0:
            raise ValueError("threshold must be positive")


@dataclass(frozen=True)
class WindowResult:
    duration_seconds: int
    total: int
    errors: int
    error_rate: float
    burn_rate: float


@dataclass(frozen=True)
class AlertResult:
    name: str
    severity: str
    threshold: float
    firing: bool
    long_window: WindowResult
    short_window: WindowResult


@dataclass(frozen=True)
class Analysis:
    objective: float
    start: datetime
    end: datetime
    total: int
    errors: int
    availability: float
    allowed_error_rate: float
    error_budget_consumed: float
    alerts: tuple[AlertResult, ...]

    @property
    def firing_alerts(self) -> tuple[AlertResult, ...]:
        return tuple(alert for alert in self.alerts if alert.firing)


DEFAULT_POLICIES = (
    AlertPolicy("fast-burn", timedelta(hours=1), timedelta(minutes=5), 14.4, "page"),
    AlertPolicy("slow-burn", timedelta(hours=6), timedelta(minutes=30), 6.0, "page"),
    AlertPolicy("budget-trend", timedelta(days=3), timedelta(hours=6), 1.0, "ticket"),
)


def analyze(
    samples: Iterable[Sample],
    objective: float,
    policies: Iterable[AlertPolicy] = DEFAULT_POLICIES,
) -> Analysis:
    """Analyze request buckets ending at the newest sample timestamp."""

    if not 0 < objective < 1:
        raise ValueError("objective must be greater than 0 and less than 1")

    ordered = sorted(samples, key=lambda sample: sample.timestamp)
    if not ordered:
        raise ValueError("at least one sample is required")
    if len({sample.timestamp for sample in ordered}) != len(ordered):
        raise ValueError("sample timestamps must be unique")

    total = sum(sample.total for sample in ordered)
    errors = sum(sample.errors for sample in ordered)
    if total == 0:
        raise ValueError("at least one request is required")

    allowed_error_rate = 1 - objective
    end = ordered[-1].timestamp.astimezone(timezone.utc)
    alert_results = tuple(
        _evaluate_policy(ordered, end, allowed_error_rate, policy) for policy in policies
    )

    return Analysis(
        objective=objective,
        start=ordered[0].timestamp.astimezone(timezone.utc),
        end=end,
        total=total,
        errors=errors,
        availability=1 - (errors / total),
        allowed_error_rate=allowed_error_rate,
        error_budget_consumed=(errors / total) / allowed_error_rate,
        alerts=alert_results,
    )


def _evaluate_policy(
    samples: list[Sample],
    end: datetime,
    allowed_error_rate: float,
    policy: AlertPolicy,
) -> AlertResult:
    long_result = _window(samples, end, policy.long_window, allowed_error_rate)
    short_result = _window(samples, end, policy.short_window, allowed_error_rate)
    firing = (
        long_result.total > 0
        and short_result.total > 0
        and long_result.burn_rate >= policy.threshold
        and short_result.burn_rate >= policy.threshold
    )
    return AlertResult(
        name=policy.name,
        severity=policy.severity,
        threshold=policy.threshold,
        firing=firing,
        long_window=long_result,
        short_window=short_result,
    )


def _window(
    samples: list[Sample],
    end: datetime,
    duration: timedelta,
    allowed_error_rate: float,
) -> WindowResult:
    start = end - duration
    selected = [sample for sample in samples if start < sample.timestamp <= end]
    total = sum(sample.total for sample in selected)
    errors = sum(sample.errors for sample in selected)
    error_rate = errors / total if total else 0.0
    return WindowResult(
        duration_seconds=int(duration.total_seconds()),
        total=total,
        errors=errors,
        error_rate=error_rate,
        burn_rate=error_rate / allowed_error_rate,
    )
