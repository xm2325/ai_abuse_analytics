from __future__ import annotations

from pathlib import Path
import pandas as pd

REQUIRED_TELEMETRY = {
    "request_id",
    "timestamp",
    "account_id",
    "device_hash",
    "ip_hash",
    "payment_hash",
    "token_hash",
    "model_family",
    "prompt_chars",
    "completion_chars",
    "completion_accepted",
    "prompt_injection_signal",
    "content_policy_signal",
    "safety_blocked",
    "entitlement_limit",
}


def run_data_contracts(data_dir: str | Path, out_dir: str | Path) -> pd.DataFrame:
    data_dir = Path(data_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(data_dir / "telemetry.csv", keep_default_na=False)
    a = pd.read_csv(data_dir / "accounts.csv", keep_default_na=False)
    findings: list[dict] = []

    missing_cols = sorted(REQUIRED_TELEMETRY - set(t.columns))
    findings.append({"contract":"telemetry_schema","status":"fail" if missing_cols else "pass","severity":"critical" if missing_cols else "info","observed":"missing=" + ",".join(missing_cols) if missing_cols else "all required columns present","recommended_action":"block downstream refresh and repair producer contract" if missing_cols else "none"})

    dup_rate = 1 - t.request_id.nunique() / max(1, len(t))
    findings.append({"contract":"request_id_uniqueness","status":"fail" if dup_rate > 0 else "pass","severity":"high" if dup_rate > 0 else "info","observed":f"duplicate_rate={dup_rate:.6f}","recommended_action":"deduplicate at ingestion and identify producer retry semantics" if dup_rate > 0 else "none"})

    orphan_rate = (~t.account_id.isin(set(a.account_id))).mean()
    findings.append({"contract":"account_referential_integrity","status":"fail" if orphan_rate > 0.001 else "pass","severity":"high" if orphan_rate > 0.001 else "info","observed":f"orphan_event_rate={orphan_rate:.6f}","recommended_action":"repair account join key or late-arriving dimension handling" if orphan_rate > 0.001 else "none"})

    allowed_models = {"code_completion", "chat", "agent"}
    invalid_model_rate = (~t.model_family.isin(allowed_models)).mean()
    findings.append({"contract":"model_family_domain","status":"fail" if invalid_model_rate > 0 else "pass","severity":"medium" if invalid_model_rate > 0 else "info","observed":f"invalid_rate={invalid_model_rate:.6f}","recommended_action":"update taxonomy/data contract before consuming new surface" if invalid_model_rate > 0 else "none"})

    ts = pd.to_datetime(t.timestamp, utc=True, format="mixed")
    tmp = t.assign(event_date=ts.dt.date.astype(str))
    for signal in ["ip_hash", "device_hash", "token_hash", "payment_hash"]:
        daily = tmp.groupby("event_date")[signal].apply(lambda s: 1 - s.astype(str).eq("").mean())
        baseline = float(daily.head(min(14, len(daily))).median())
        worst = float(daily.min())
        drop = baseline - worst
        findings.append({"contract":f"{signal}_daily_coverage","status":"fail" if drop > 0.05 else "warn" if drop > 0.02 else "pass","severity":"critical" if drop > 0.10 else "high" if drop > 0.05 else "medium" if drop > 0.02 else "info","observed":f"baseline={baseline:.3%}; worst={worst:.3%}; drop={drop:.3%}","recommended_action":"trace producer/integration change, annotate affected dates, and suppress model-policy changes until coverage recovers" if drop > 0.02 else "monitor"})

    out = pd.DataFrame(findings)
    out.to_csv(out_dir / "data_quality_findings.csv", index=False)
    return out


def build_signal_backlog(out_dir: str | Path) -> pd.DataFrame:
    rows = [
        {"priority":"P0","signal_or_integration":"known_automation_identity","analytical_problem":"legitimate CI/agent automation can resemble scripted misuse","proposed_source":"approved automation / integration registry","decision_supported":"suppress false positives before human review","privacy_class":"account/product metadata","partner":"Anti-Abuse Engineering + Product"},
        {"priority":"P0","signal_or_integration":"managed_network_context","analytical_problem":"shared enterprise egress can resemble credential sharing","proposed_source":"organization-managed network or enterprise context flag","decision_supported":"interpret IP/device dispersion safely","privacy_class":"derived network context","partner":"Security + Engineering + CELA"},
        {"priority":"P1","signal_or_integration":"token_lifecycle_events","analytical_problem":"token reuse cannot be interpreted without issue/revoke/rotation context","proposed_source":"authentication lifecycle event stream","decision_supported":"separate misuse from expected token rotation/integration behavior","privacy_class":"security telemetry","partner":"Identity/Security Engineering"},
        {"priority":"P1","signal_or_integration":"review_and_appeal_feedback","analytical_problem":"detection quality drifts if cleared and overturned cases do not return to analytics","proposed_source":"case management outcomes with matured-label timestamp","decision_supported":"threshold calibration and rule retirement","privacy_class":"restricted investigation metadata","partner":"Trust & Safety Operations + CELA"},
    ]
    out = pd.DataFrame(rows)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out.to_csv(Path(out_dir) / "signal_integration_backlog.csv", index=False)
    return out
