from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .analyzer import Sample


def read_csv(path: Path) -> list[Sample]:
    """Read timestamp,total,errors request buckets from a CSV file."""

    try:
        handle = path.open(encoding="utf-8", newline="")
    except OSError as exc:
        raise ValueError(f"cannot read input file: {path}") from exc

    with handle:
        reader = csv.DictReader(handle)
        required = {"timestamp", "total", "errors"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("CSV must contain timestamp,total,errors columns")

        samples: list[Sample] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                timestamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                total = int(row["total"])
                errors = int(row["errors"])
                samples.append(Sample(timestamp=timestamp, total=total, errors=errors))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid sample on CSV line {line_number}: {exc}") from exc
    return samples
