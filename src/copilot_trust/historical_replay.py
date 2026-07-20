from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


def _binary_counts(y: pd.Series, pred: pd.Series) -> dict[str, float | int]:
    y = y.astype(int).to_numpy()
    p = pred.astype(bool).to_numpy()
    tp = int(((y == 1) & p).sum())
    fp = int(((y == 0) & p).sum())
    tn = int(((y == 0) & ~p).sum())
    fn = int(((y == 1) & ~p).sum())
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": tp / max(1, tp + fp),
        "recall": tp / max(1, tp + fn),
        "false_positive_rate": fp / max(1, fp + tn),
        "false_negative_rate": fn / max(1, fn + tp),
    }


def _window_features(events: pd.DataFrame, accounts: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    w = events[(events.timestamp >= start) & (events.timestamp < end + pd.Timedelta(days=1))].copy()
    if w.empty:
        base = accounts[["account_id", "ground_truth_abuse_type", "managed_infrastructure", "legitimate_profile"]].copy()
        for c in ["requests", "active_days", "unique_devices", "unique_ips", "policy_signal_rate", "injection_rate", "block_rate", "agent_share", "overnight_share", "requests_per_active_day"]:
            base[c] = 0.0
        return base

    w["event_date"] = w.timestamp.dt.floor("D")
    w["overnight"] = ((w.timestamp.dt.hour < 6) | (w.timestamp.dt.hour >= 23)).astype(int)
    w["agent"] = w.model_family.eq("agent").astype(int)
    agg = w.groupby("account_id").agg(
        requests=("request_id", "count"),
        active_days=("event_date", "nunique"),
        unique_devices=("device_hash", lambda s: s.replace("", np.nan).nunique()),
        unique_ips=("ip_hash", lambda s: s.replace("", np.nan).nunique()),
        policy_signal_rate=("content_policy_signal", "mean"),
        injection_rate=("prompt_injection_signal", "mean"),
        block_rate=("safety_blocked", "mean"),
        agent_share=("agent", "mean"),
        overnight_share=("overnight", "mean"),
    ).reset_index()
    agg["requests_per_active_day"] = agg.requests / agg.active_days.clip(lower=1)
    base = accounts[["account_id", "ground_truth_abuse_type", "managed_infrastructure", "legitimate_profile"]].merge(agg, on="account_id", how="left")
    numeric = ["requests", "active_days", "unique_devices", "unique_ips", "policy_signal_rate", "injection_rate", "block_rate", "agent_share", "overnight_share", "requests_per_active_day"]
    base[numeric] = base[numeric].fillna(0.0)
    return base


def _rule_map(g: pd.DataFrame, velocity_cut: float) -> dict[str, pd.Series]:
    return {
        "scripted_usage_v1": (g.requests_per_active_day >= velocity_cut) & (g.overnight_share >= 0.08),
        "identity_dispersion_v1": (g.unique_devices >= 5) & (g.unique_ips >= 7),
        "policy_signal_v1": g.policy_signal_rate >= 0.030,
        "policy_signal_v2": ((g.policy_signal_rate >= 0.020) & (g.injection_rate >= 0.015)) | ((g.policy_signal_rate >= 0.025) & (g.agent_share >= 0.35)),
    }


def build_historical_replay(
    data_dir: str | Path,
    out_dir: str | Path,
    *,
    lookback_days: int = 7,
    checkpoint_every_days: int = 7,
    label_maturity_days: int = 7,
    case_cooldown_days: int = 14,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Replay rule versions over time without using events that occur after each checkpoint.

    Ground-truth labels are used only for synthetic benchmark diagnostics. Operational label metrics use
    review outcomes that were already mature at the replay checkpoint.
    """
    data_dir, out = Path(data_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(data_dir / "telemetry.csv")
    accounts = pd.read_csv(data_dir / "accounts.csv")
    reviews = pd.read_csv(data_dir / "reviews.csv")
    events["timestamp"] = pd.to_datetime(events.timestamp, utc=True, format="mixed")
    reviews["review_date"] = pd.to_datetime(reviews.review_date, utc=True, format="mixed")
    accounts["label"] = accounts.ground_truth_abuse_type.ne("legitimate").astype(int)

    first_day = events.timestamp.min().floor("D")
    last_day = events.timestamp.max().floor("D")
    baseline_end = min(first_day + pd.Timedelta(days=20), last_day)
    baseline = _window_features(events, accounts, first_day, baseline_end)
    velocity_cut = float(max(20.0, baseline.requests_per_active_day.quantile(0.90)))

    checkpoint_start = min(first_day + pd.Timedelta(days=20), last_day)
    checkpoints = list(pd.date_range(checkpoint_start, last_day, freq=f"{checkpoint_every_days}D"))
    if not checkpoints or checkpoints[-1] != last_day:
        checkpoints.append(last_day)

    metric_rows: list[dict] = []
    arrival_rows: list[dict] = []
    last_arrival: dict[str, pd.Timestamp] = {}

    for checkpoint in checkpoints:
        window_start = checkpoint - pd.Timedelta(days=lookback_days - 1)
        g = _window_features(events, accounts, window_start, checkpoint)
        g["label"] = g.ground_truth_abuse_type.ne("legitimate").astype(int)
        rules = _rule_map(g, velocity_cut)
        phase = "pre_mitigation" if checkpoint < first_day + pd.Timedelta(days=35) else "post_mitigation" if checkpoint < first_day + pd.Timedelta(days=46) else "emerging_campaign"
        mature_cut = checkpoint - pd.Timedelta(days=label_maturity_days)
        mature = reviews[reviews.review_date <= mature_cut].copy()
        mature["observed_label"] = mature.final_outcome.eq("confirmed_abuse").astype(int)
        observed = mature.sort_values("review_date").drop_duplicates("account_id", keep="last").set_index("account_id")["observed_label"] if len(mature) else pd.Series(dtype=int)

        account_triggers: dict[str, list[str]] = {}
        for rule_id, pred in rules.items():
            m = _binary_counts(g.label, pred)
            triggered = g.loc[pred, "account_id"]
            reviewed_triggered = triggered[triggered.isin(observed.index)]
            observed_precision = float(observed.loc[reviewed_triggered].mean()) if len(reviewed_triggered) else np.nan
            metric_rows.append({
                "checkpoint": checkpoint.date().isoformat(),
                "window_start": window_start.date().isoformat(),
                "window_end": checkpoint.date().isoformat(),
                "phase": phase,
                "rule_id": rule_id,
                "threshold_source": "first_21_days_frozen" if rule_id == "scripted_usage_v1" else "policy_defined_static",
                "velocity_cut": velocity_cut if rule_id == "scripted_usage_v1" else np.nan,
                "accounts_evaluated": int(len(g)),
                "accounts_triggered": int(pred.sum()),
                "review_workload_share": float(pred.mean()),
                **m,
                "matured_reviewed_triggers": int(len(reviewed_triggered)),
                "matured_review_precision": observed_precision,
                "matured_label_coverage_of_triggers": float(len(reviewed_triggered) / max(1, int(pred.sum()))),
                "lookahead_protection": "events_after_checkpoint_excluded",
            })
            for account_id in triggered:
                account_triggers.setdefault(str(account_id), []).append(rule_id)

        g_idx = g.set_index("account_id")
        for account_id, triggered_rules in account_triggers.items():
            previous = last_arrival.get(account_id)
            if previous is not None and (checkpoint - previous).days < case_cooldown_days:
                continue
            r = g_idx.loc[account_id]
            signal_strength = min(1.0, 0.22 * len(triggered_rules) + 1.4 * float(r.policy_signal_rate) + 0.9 * float(r.injection_rate) + 0.25 * float(r.overnight_share))
            risk_proxy = float(min(0.99, 0.35 + 0.55 * signal_strength))
            priority = "P0" if risk_proxy >= 0.90 else "P1" if risk_proxy >= 0.75 else "P2" if risk_proxy >= 0.60 else "P3"
            estimated_minutes = int(24 + 7 * max(0, len(triggered_rules) - 1) + (12 if any("identity" in x for x in triggered_rules) else 0))
            arrival_rows.append({
                "case_id": f"replay_{checkpoint.strftime('%Y%m%d')}_{account_id}",
                "account_id": account_id,
                "arrival_date": checkpoint.date().isoformat(),
                "phase": phase,
                "triggered_rules": "|".join(sorted(triggered_rules)),
                "rule_count": int(len(triggered_rules)),
                "risk_proxy": risk_proxy,
                "priority_tier": priority,
                "estimated_review_minutes": estimated_minutes,
                "managed_infrastructure": int(r.managed_infrastructure),
                "legitimate_profile": str(r.legitimate_profile),
                "benchmark_known_abuse": int(r.label),
                "matured_review_label_available": int(account_id in observed.index),
                "matured_review_label": int(observed.loc[account_id]) if account_id in observed.index else np.nan,
            })
            last_arrival[account_id] = checkpoint

    replay = pd.DataFrame(metric_rows)
    arrivals = pd.DataFrame(arrival_rows)
    summary = replay.groupby(["rule_id", "phase"], as_index=False).agg(
        checkpoints=("checkpoint", "count"),
        mean_triggered=("accounts_triggered", "mean"),
        mean_review_workload_share=("review_workload_share", "mean"),
        benchmark_precision=("precision", "mean"),
        benchmark_recall=("recall", "mean"),
        benchmark_fpr=("false_positive_rate", "mean"),
        matured_reviewed_triggers=("matured_reviewed_triggers", "sum"),
        mean_matured_label_coverage=("matured_label_coverage_of_triggers", "mean"),
    )
    replay.to_csv(out / "historical_rule_replay.csv", index=False)
    arrivals.to_csv(out / "historical_case_arrivals.csv", index=False)
    summary.to_csv(out / "historical_rule_replay_summary.csv", index=False)
    return replay, arrivals, summary
