from __future__ import annotations

import json
from dataclasses import asdict

from .analyzer import Analysis


def render_text(analysis: Analysis) -> str:
    lines = [
        f"SLO objective: {analysis.objective:.5%}",
        f"Observed availability: {analysis.availability:.5%}",
        f"Requests: {analysis.total} ({analysis.errors} errors)",
        f"Error budget consumed: {analysis.error_budget_consumed:.2f}x",
        "Alerts:",
    ]
    for alert in analysis.alerts:
        state = "FIRING" if alert.firing else "ok"
        lines.append(
            f"- {alert.name} [{state}] long={alert.long_window.burn_rate:.2f}x "
            f"short={alert.short_window.burn_rate:.2f}x threshold={alert.threshold:.2f}x"
        )
    return "\n".join(lines)


def render_json(analysis: Analysis) -> str:
    payload = asdict(analysis)
    payload["start"] = analysis.start.isoformat()
    payload["end"] = analysis.end.isoformat()
    payload["firing_alert_count"] = len(analysis.firing_alerts)
    return json.dumps(payload, indent=2, sort_keys=True)


def render_markdown(analysis: Analysis) -> str:
    rows = [
        "# SLO burn-rate report",
        "",
        f"- Objective: **{analysis.objective:.5%}**",
        f"- Observed availability: **{analysis.availability:.5%}**",
        f"- Requests: **{analysis.total}** ({analysis.errors} errors)",
        f"- Error budget consumed: **{analysis.error_budget_consumed:.2f}x**",
        "",
        "| Policy | Severity | Long burn | Short burn | Threshold | State |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for alert in analysis.alerts:
        state = "FIRING" if alert.firing else "OK"
        rows.append(
            f"| {alert.name} | {alert.severity} | {alert.long_window.burn_rate:.2f}x | "
            f"{alert.short_window.burn_rate:.2f}x | {alert.threshold:.2f}x | {state} |"
        )
    return "\n".join(rows)
