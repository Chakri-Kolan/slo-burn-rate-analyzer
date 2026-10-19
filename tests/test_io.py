from pathlib import Path

import pytest

from slo_burn_rate.io import read_csv


def test_read_csv(tmp_path: Path) -> None:
    path = tmp_path / "samples.csv"
    path.write_text(
        "timestamp,total,errors\n2026-01-01T00:00:00Z,100,2\n",
        encoding="utf-8",
    )

    samples = read_csv(path)

    assert len(samples) == 1
    assert samples[0].total == 100
    assert samples[0].errors == 2
    assert samples[0].timestamp.utcoffset() is not None


def test_read_csv_requires_columns(tmp_path: Path) -> None:
    path = tmp_path / "samples.csv"
    path.write_text("timestamp,total\n2026-01-01T00:00:00Z,100\n", encoding="utf-8")

    with pytest.raises(ValueError, match="columns"):
        read_csv(path)


def test_read_csv_reports_line_number(tmp_path: Path) -> None:
    path = tmp_path / "samples.csv"
    path.write_text("timestamp,total,errors\nbad,100,0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 2"):
        read_csv(path)


def test_read_csv_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot read"):
        read_csv(tmp_path / "missing.csv")
