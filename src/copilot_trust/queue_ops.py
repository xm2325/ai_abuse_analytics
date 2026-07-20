from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def evaluate_queue_operations(scores: pd.DataFrame, data_dir: str | Path, out_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create an operational queue view with age/SLA bands and capacity scenarios.

    Synthetic event timestamps are used as a benchmark clock; this is not a real service-level report.
    """
    data_dir, out = Path(data_dir), Path(out_dir)
    events = pd.read_csv(data_dir / "telemetry.csv")
    events["timestamp"] = pd.to_datetime(events.timestamp, format="mixed", utc=True)
    clock = events.timestamp.max() + pd.Timedelta(hours=12)
    last_seen = events.groupby("account_id").timestamp.max()

    q = scores[scores.flagged.eq(1)].copy()
    q["last_signal_at"] = q.account_id.map(last_seen)
    q["queue_age_hours"] = (clock - q.last_signal_at).dt.total_seconds() / 3600
    q["priority_tier"] = pd.cut(q.risk_score, [-np.inf, .60, .75, .90, np.inf], labels=["P3", "P2", "P1", "P0"])
    sla = {"P0": 4, "P1": 12, "P2": 24, "P3": 48}
    q["sla_hours"] = q.priority_tier.astype(str).map(sla).fillna(48)
    q["sla_breached"] = q.queue_age_hours > q.sla_hours
    q["estimated_review_minutes"] = np.where(q.reason_codes.str.contains("shared_|device_|ip_", regex=True), 35, 22)
    q["review_value"] = q.risk_score / q.estimated_review_minutes
    q = q.sort_values(["priority_tier", "review_value"], ascending=[True, False])
    q.to_csv(out / "queue_sla_snapshot.csv", index=False)

    scenarios = []
    for analyst_hours in [4, 8, 16, 32]:
        budget = analyst_hours * 60
        ordered = q.sort_values("review_value", ascending=False)
        cum = ordered.estimated_review_minutes.cumsum()
        selected = ordered[cum <= budget]
        scenarios.append({
            "analyst_hours": analyst_hours,
            "cases_reviewable": int(len(selected)),
            "share_of_flagged_queue": float(len(selected) / max(1, len(q))),
            "known_abuse_recall_within_flagged_queue": float(selected.label.sum() / max(1, q.label.sum())),
            "expected_precision_from_benchmark_labels": float(selected.label.mean()) if len(selected) else 0.0,
            "p0_p1_coverage": float(selected.priority_tier.astype(str).isin(["P0", "P1"]).sum() / max(1, q.priority_tier.astype(str).isin(["P0", "P1"]).sum())),
        })
    cap = pd.DataFrame(scenarios)
    cap.to_csv(out / "queue_capacity_plan.csv", index=False)
    return q, cap
