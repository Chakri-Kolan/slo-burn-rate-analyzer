from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from slo_burn_rate.analyzer import AlertPolicy, Sample, analyze

NOW = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def sample(minutes_ago: int, total: int = 1_000, errors: int = 0) -> Sample:
    return Sample(NOW - timedelta(minutes=minutes_ago), total, errors)


def test_analysis_calculates_availability_and_budget() -> None:
    result = analyze([sample(1, errors=1), sample(0, errors=0)], objective=0.999)

    assert result.total == 2_000
    assert result.errors == 1
    assert result.availability == pytest.approx(0.9995)
    assert result.error_budget_consumed == pytest.approx(0.5)


def test_fast_burn_requires_both_windows_to_cross_threshold() -> None:
    policy = AlertPolicy("fast", timedelta(hours=1), timedelta(minutes=5), 10, "page")
    result = analyze(
        [sample(50, errors=20), sample(4, errors=20), sample(0, errors=20)],
        objective=0.999,
        policies=[policy],
    )

    alert = result.alerts[0]
    assert alert.long_window.burn_rate == pytest.approx(20)
    assert alert.short_window.burn_rate == pytest.approx(20)
    assert alert.firing is True


def test_alert_does_not_fire_when_short_window_recovers() -> None:
    policy = AlertPolicy("fast", timedelta(hours=1), timedelta(minutes=5), 10, "page")
    result = analyze(
        [sample(50, errors=100), sample(4), sample(0)],
        objective=0.999,
        policies=[policy],
    )

    assert result.alerts[0].long_window.burn_rate > 10
    assert result.alerts[0].short_window.burn_rate == 0
    assert result.alerts[0].firing is False


@pytest.mark.parametrize("objective", [0, 1, -0.1, 1.1])
def test_invalid_objective_is_rejected(objective: float) -> None:
    with pytest.raises(ValueError, match="objective"):
        analyze([sample(0)], objective)


def test_empty_or_zero_traffic_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one sample"):
        analyze([], 0.999)
    with pytest.raises(ValueError, match="at least one request"):
        analyze([sample(0, total=0)], 0.999)


def test_duplicate_timestamps_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        analyze([sample(0), sample(0)], 0.999)


@pytest.mark.parametrize(
    ("total", "errors", "message"),
    [(-1, 0, "negative"), (10, -1, "negative"), (1, 2, "exceed")],
)
def test_invalid_sample_counters_are_rejected(total: int, errors: int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Sample(NOW, total, errors)


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone"):
        Sample(datetime(2026, 1, 1), 1, 0)


def test_invalid_alert_policy_is_rejected() -> None:
    with pytest.raises(ValueError, match="short_window"):
        AlertPolicy("bad", timedelta(minutes=5), timedelta(minutes=5), 1, "page")
