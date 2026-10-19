from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .analyzer import analyze
from .io import read_csv
from .report import render_json, render_markdown, render_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slo-burn-rate",
        description="Analyze SLO error-budget consumption from request counter buckets.",
    )
    parser.add_argument("input", type=Path, help="CSV with timestamp,total,errors columns")
    parser.add_argument(
        "--objective",
        type=float,
        default=0.999,
        help="Availability objective as a decimal (default: 0.999)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "markdown"),
        default="text",
        help="Report format",
    )
    parser.add_argument(
        "--fail-on-alert",
        action="store_true",
        help="Exit with status 2 when any multi-window alert is firing",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        analysis = analyze(read_csv(args.input), args.objective)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    renderer = {
        "text": render_text,
        "json": render_json,
        "markdown": render_markdown,
    }[args.format]
    print(renderer(analysis))
    return 2 if args.fail_on_alert and analysis.firing_alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
