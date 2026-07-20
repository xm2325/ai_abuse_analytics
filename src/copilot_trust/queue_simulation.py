from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def _priority_rank(tier: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(str(tier), 4)


def simulate_queue_capacity(
    arrivals: pd.DataFrame,
    out_dir: str | Path,
    *,
    analyst_fte_scenarios: tuple[float, ...] = (0.5, 1.0, 2.0),
    productive_review_minutes_per_fte_day: int = 300,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Discrete daily queue simulation using only arrival date, priority, and estimated review effort.

    The benchmark models human-investigation capacity; it does not use benchmark labels to prioritize cases.
    """
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    if arrivals.empty:
        daily = pd.DataFrame(columns=["analyst_fte", "date", "arrivals", "completed", "backlog", "unresolved_sla_breaches", "oldest_case_age_days", "utilization"])
        summary = pd.DataFrame(columns=["analyst_fte", "cases_arrived", "cases_completed", "final_backlog", "max_backlog", "sla_breach_rate_completed", "p95_time_to_review_hours", "mean_utilization"])
        daily.to_csv(out / "queue_simulation_daily.csv", index=False); summary.to_csv(out / "queue_simulation_summary.csv", index=False)
        return daily, summary

    base = arrivals.copy()
    base["arrival_date"] = pd.to_datetime(base.arrival_date, utc=True, format="mixed").dt.floor("D")
    sla_hours = {"P0": 4, "P1": 12, "P2": 24, "P3": 48}
    start = base.arrival_date.min()
    end = base.arrival_date.max() + pd.Timedelta(days=14)
    days = pd.date_range(start, end, freq="D", tz="UTC")
    daily_rows, summary_rows = [], []

    for fte in analyst_fte_scenarios:
        pending: list[dict] = []
        completed_records: list[dict] = []
        max_backlog = 0
        utilizations = []
        for day in days:
            todays = base[base.arrival_date.eq(day)]
            for row in todays.to_dict("records"):
                row["remaining_minutes"] = float(row["estimated_review_minutes"])
                pending.append(row)

            capacity = float(productive_review_minutes_per_fte_day * fte)
            initial_capacity = capacity
            pending.sort(key=lambda r: (_priority_rank(r["priority_tier"]), -float(r["risk_proxy"]), pd.Timestamp(r["arrival_date"])))
            completed_today = 0
            i = 0
            while i < len(pending) and capacity > 1e-9:
                case = pending[i]
                work = min(float(case["remaining_minutes"]), capacity)
                case["remaining_minutes"] -= work
                capacity -= work
                if case["remaining_minutes"] <= 1e-9:
                    resolved_at = day + pd.Timedelta(hours=17)
                    delay_hours = max(0.0, (resolved_at - pd.Timestamp(case["arrival_date"])).total_seconds() / 3600)
                    completed_records.append({**case, "resolved_at": resolved_at, "time_to_review_hours": delay_hours, "sla_breached_at_completion": int(delay_hours > sla_hours.get(str(case["priority_tier"]), 48))})
                    pending.pop(i)
                    completed_today += 1
                else:
                    i += 1

            ages_hours = [max(0.0, ((day + pd.Timedelta(hours=23, minutes=59)) - pd.Timestamp(c["arrival_date"])).total_seconds() / 3600) for c in pending]
            breaches = sum(age > sla_hours.get(str(c["priority_tier"]), 48) for age, c in zip(ages_hours, pending))
            utilization = 0.0 if initial_capacity <= 0 else (initial_capacity - capacity) / initial_capacity
            utilizations.append(utilization)
            max_backlog = max(max_backlog, len(pending))
            daily_rows.append({
                "analyst_fte": fte,
                "date": day.date().isoformat(),
                "arrivals": int(len(todays)),
                "completed": int(completed_today),
                "backlog": int(len(pending)),
                "unresolved_sla_breaches": int(breaches),
                "oldest_case_age_days": float(max(ages_hours) / 24) if ages_hours else 0.0,
                "utilization": float(utilization),
            })

        completed_df = pd.DataFrame(completed_records)
        if len(completed_df):
            p95 = float(completed_df.time_to_review_hours.quantile(0.95))
            breach_rate = float(completed_df.sla_breached_at_completion.mean())
        else:
            p95, breach_rate = np.nan, np.nan
        summary_rows.append({
            "analyst_fte": fte,
            "productive_review_minutes_per_fte_day": productive_review_minutes_per_fte_day,
            "cases_arrived": int(len(base)),
            "cases_completed": int(len(completed_df)),
            "final_backlog": int(len(pending)),
            "max_backlog": int(max_backlog),
            "sla_breach_rate_completed": breach_rate,
            "p95_time_to_review_hours": p95,
            "mean_utilization": float(np.mean(utilizations)) if utilizations else 0.0,
            "simulation_boundary": "synthetic capacity planning; benchmark labels are not used for prioritization",
        })

    daily = pd.DataFrame(daily_rows)
    summary = pd.DataFrame(summary_rows)
    daily.to_csv(out / "queue_simulation_daily.csv", index=False)
    summary.to_csv(out / "queue_simulation_summary.csv", index=False)
    return daily, summary
