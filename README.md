# SLO Burn-Rate Analyzer

Offline Python CLI for calculating availability, error-budget consumption, and
multi-window burn-rate alerts from request counter buckets. It uses no hosted or
paid services.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --editable ".[dev]"
slo-burn-rate examples/requests.csv --objective 0.999
```

Input is CSV with `timestamp,total,errors` columns. Timestamps must be ISO 8601
with a timezone. Each row represents a completed observation bucket.

```bash
slo-burn-rate examples/requests.csv --format json
slo-burn-rate examples/requests.csv --format markdown
slo-burn-rate examples/requests.csv --fail-on-alert
```

`--fail-on-alert` exits with status 2 when a multi-window policy is firing, so
the tool can act as a local or CI quality gate. Invalid input exits with status 1.

## Validate

```bash
ruff check .
pytest
```

The default policies compare both long and short burn-rate windows to avoid
alerting on a stale spike or a brief isolated error burst.
