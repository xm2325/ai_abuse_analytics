from __future__ import annotations

from pathlib import Path
import hashlib
import numpy as np
import pandas as pd


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def build_synthetic_entitlement_ledger(data_dir: str | Path, cycle_days: int = 28) -> pd.DataFrame:
    """Build a privacy-safe synthetic billing/entitlement ledger from the benchmark accounts.

    The ledger is deliberately separate from telemetry so analysis can test integration, cycle alignment,
    shared billing context, and entitlement-pressure hypotheses without treating event fields as billing truth.
    """
    data = Path(data_dir)
    accounts = pd.read_csv(data / "accounts.csv", keep_default_na=False)
    telemetry = pd.read_csv(data / "telemetry.csv", keep_default_na=False)
    telemetry["timestamp"] = pd.to_datetime(telemetry.timestamp, utc=True, format="mixed")
    first_day = telemetry.timestamp.min().floor("D")
    last_day = telemetry.timestamp.max().floor("D")
    primary_payment = telemetry.loc[telemetry.payment_hash.ne("")].groupby("account_id").payment_hash.first()
    limit_map = telemetry.groupby("account_id").entitlement_limit.max()

    rows = []
    cycle_start = first_day
    cycle_index = 0
    while cycle_start <= last_day:
        cycle_end = min(cycle_start + pd.Timedelta(days=cycle_days - 1), last_day)
        for i, r in accounts.reset_index(drop=True).iterrows():
            payment = str(primary_payment.get(r.account_id, _hash(f"payment:{r.account_id}")))
            # Legitimate managed accounts sometimes share an organization billing context.
            if r.ground_truth_abuse_type == "legitimate" and int(r.managed_infrastructure) == 1 and i % 9 == 0:
                billing_family = _hash(f"managed-billing:{i % 5}")
                billing_context = "managed_shared_billing"
            else:
                billing_family = payment
                billing_context = "account_billing"
            base_limit = int(limit_map.get(r.account_id, 100))
            rows.append({
                "account_id": r.account_id,
                "cycle_index": cycle_index,
                "cycle_start": cycle_start.date().isoformat(),
                "cycle_end": cycle_end.date().isoformat(),
                "plan": r.plan,
                "billing_status": r.billing_status,
                "entitlement_limit_per_active_day": base_limit,
                "billing_family_ref": billing_family,
                "billing_context": billing_context,
                "managed_infrastructure": int(r.managed_infrastructure),
                "source_system": "synthetic_entitlement_ledger",
            })
        cycle_start = cycle_start + pd.Timedelta(days=cycle_days)
        cycle_index += 1
    ledger = pd.DataFrame(rows)
    ledger.to_csv(data / "entitlements.csv", index=False)
    return ledger


def evaluate_entitlement_abuse(data_dir: str | Path, out_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Evaluate quota/entitlement pressure while preserving legitimate shared-billing explanations."""
    data, out = Path(data_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    accounts = pd.read_csv(data / "accounts.csv", keep_default_na=False)
    telemetry = pd.read_csv(data / "telemetry.csv", keep_default_na=False)
    ledger = pd.read_csv(data / "entitlements.csv", keep_default_na=False)
    telemetry["timestamp"] = pd.to_datetime(telemetry.timestamp, utc=True, format="mixed")
    ledger["cycle_start"] = pd.to_datetime(ledger.cycle_start, utc=True)
    ledger["cycle_end"] = pd.to_datetime(ledger.cycle_end, utc=True)

    usage_rows = []
    for _, e in ledger.iterrows():
        mask = telemetry.account_id.eq(e.account_id) & telemetry.timestamp.dt.floor("D").between(e.cycle_start, e.cycle_end)
        w = telemetry.loc[mask]
        active_days = int(w.timestamp.dt.date.nunique()) if len(w) else 0
        requests = int(len(w))
        effective_allowance = int(e.entitlement_limit_per_active_day) * max(1, active_days)
        usage_rows.append({
            "account_id": e.account_id,
            "cycle_index": int(e.cycle_index),
            "cycle_start": e.cycle_start.date().isoformat(),
            "cycle_end": e.cycle_end.date().isoformat(),
            "billing_family_ref": e.billing_family_ref,
            "billing_context": e.billing_context,
            "plan": e.plan,
            "managed_infrastructure": int(e.managed_infrastructure),
            "requests": requests,
            "active_days": active_days,
            "effective_allowance": effective_allowance,
            "usage_ratio": requests / max(1, effective_allowance),
            "near_limit": int(requests / max(1, effective_allowance) >= 0.80),
        })
    usage = pd.DataFrame(usage_rows).merge(accounts[["account_id", "ground_truth_abuse_type"]], on="account_id", how="left")

    family = usage.groupby(["cycle_index", "cycle_start", "cycle_end", "billing_family_ref"], as_index=False).agg(
        family_accounts=("account_id", "nunique"),
        combined_requests=("requests", "sum"),
        combined_allowance=("effective_allowance", "sum"),
        near_limit_accounts=("near_limit", "sum"),
        managed_share=("managed_infrastructure", "mean"),
        legitimate_shared_billing_accounts=("billing_context", lambda s: int((s == "managed_shared_billing").sum())),
        benchmark_abuse_accounts=("ground_truth_abuse_type", lambda s: int((s != "legitimate").sum())),
    )
    family["family_usage_ratio"] = family.combined_requests / family.combined_allowance.clip(lower=1)
    family["shared_billing_context"] = ((family.managed_share >= 0.80) | (family.legitimate_shared_billing_accounts >= 2)).astype(int)
    family["candidate_multi_account_evasion"] = ((family.family_accounts >= 2) & (family.near_limit_accounts >= 2) & (family.shared_billing_context == 0)).astype(int)
    family["reason_codes"] = np.where(family.candidate_multi_account_evasion.eq(1), "multi_account_same_billing_family|simultaneous_entitlement_pressure", np.where(family.shared_billing_context.eq(1), "shared_billing_requires_enterprise_context_review", "no_multi_account_pressure"))

    suspicious = family[family.candidate_multi_account_evasion.eq(1)].copy()
    queue = usage.merge(suspicious[["cycle_index", "billing_family_ref", "family_accounts", "near_limit_accounts", "family_usage_ratio", "reason_codes"]], on=["cycle_index", "billing_family_ref"], how="inner")
    if len(queue):
        queue["priority_score"] = (0.45 * queue.usage_ratio.clip(0, 1.5) + 0.20 * (queue.family_accounts.clip(1, 5) / 5) + 0.20 * (queue.near_limit_accounts.clip(1, 4) / 4) + 0.15 * queue.family_usage_ratio.clip(0, 1.5)).clip(0, 1)
        queue = queue.sort_values(["priority_score", "cycle_index"], ascending=[False, False])
    queue = queue[[c for c in ["account_id", "cycle_index", "cycle_start", "plan", "billing_family_ref", "usage_ratio", "family_accounts", "near_limit_accounts", "family_usage_ratio", "priority_score", "reason_codes"] if c in queue.columns]]

    required = {"account_id", "cycle_index", "cycle_start", "cycle_end", "entitlement_limit_per_active_day", "billing_family_ref"}
    findings = [
        {"contract": "entitlement_schema", "status": "pass" if required.issubset(ledger.columns) else "fail", "severity": "info" if required.issubset(ledger.columns) else "critical", "observed": f"missing={sorted(required-set(ledger.columns))}", "recommended_action": "none" if required.issubset(ledger.columns) else "repair billing/entitlement integration before quota-abuse analysis"},
        {"contract": "entitlement_account_referential_integrity", "status": "pass" if ledger.account_id.isin(set(accounts.account_id)).all() else "fail", "severity": "info" if ledger.account_id.isin(set(accounts.account_id)).all() else "critical", "observed": f"orphan_rows={int((~ledger.account_id.isin(set(accounts.account_id))).sum())}", "recommended_action": "none" if ledger.account_id.isin(set(accounts.account_id)).all() else "repair account-key mapping"},
        {"contract": "entitlement_cycle_uniqueness", "status": "pass" if not ledger.duplicated(["account_id", "cycle_index"]).any() else "fail", "severity": "info" if not ledger.duplicated(["account_id", "cycle_index"]).any() else "critical", "observed": f"duplicate_account_cycles={int(ledger.duplicated(['account_id','cycle_index']).sum())}", "recommended_action": "none" if not ledger.duplicated(["account_id", "cycle_index"]).any() else "deduplicate or version entitlement events before analysis"},
    ]
    dq = pd.DataFrame(findings)
    usage.to_csv(out / "entitlement_cycle_usage.csv", index=False)
    family.to_csv(out / "billing_family_risk.csv", index=False)
    queue.to_csv(out / "entitlement_investigation_queue.csv", index=False)
    dq.to_csv(out / "entitlement_data_quality.csv", index=False)
    return usage, family, queue, dq
