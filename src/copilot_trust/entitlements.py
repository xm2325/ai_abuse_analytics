from __future__ import annotations

from pathlib import Path
import hashlib
import numpy as np
import pandas as pd


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _group_map(account_ids: list[str], prefix: str, group_size: int = 3) -> dict[str, str]:
    return {account_id: _hash(f"{prefix}:{j // group_size}") for j, account_id in enumerate(account_ids)}


def build_synthetic_entitlement_ledger(data_dir: str | Path, cycle_days: int = 28) -> pd.DataFrame:
    """Build a separate privacy-safe synthetic billing/entitlement source.

    Entitlement units use a benchmark contract independent of telemetry's legacy coarse limit field.
    This avoids treating an event payload as the billing source of truth and makes cycle-pressure tests
    meaningful while remaining explicitly synthetic.
    """
    data = Path(data_dir)
    accounts = pd.read_csv(data / "accounts.csv", keep_default_na=False).reset_index(drop=True)
    telemetry = pd.read_csv(data / "telemetry.csv", keep_default_na=False)
    telemetry["timestamp"] = pd.to_datetime(telemetry.timestamp, utc=True, format="mixed")
    first_day = telemetry.timestamp.min().floor("D")
    last_day = telemetry.timestamp.max().floor("D")
    primary_payment = telemetry.loc[telemetry.payment_hash.ne("")].groupby("account_id").payment_hash.first()
    plan_daily_units = {"free": 7, "individual": 14, "business": 22, "enterprise": 28}

    quota_ids = accounts.loc[accounts.ground_truth_abuse_type.eq("quota_evasion"), "account_id"].tolist()
    quota_family = _group_map(quota_ids, "synthetic-quota-evasion-billing", group_size=3)
    managed_legit_ids = accounts.loc[(accounts.ground_truth_abuse_type.eq("legitimate")) & accounts.managed_infrastructure.eq(1), "account_id"].tolist()
    managed_shared_ids = managed_legit_ids[: min(12, len(managed_legit_ids))]
    managed_family = _group_map(managed_shared_ids, "synthetic-managed-shared-billing", group_size=3)

    rows = []
    cycle_start = first_day
    cycle_index = 0
    while cycle_start <= last_day:
        cycle_end = min(cycle_start + pd.Timedelta(days=cycle_days - 1), last_day)
        for _, r in accounts.iterrows():
            account_id = str(r.account_id)
            payment = str(primary_payment.get(account_id, _hash(f"payment:{account_id}")))
            if account_id in quota_family:
                billing_family = quota_family[account_id]; billing_context = "synthetic_linked_billing_for_quota_evasion"
            elif account_id in managed_family:
                billing_family = managed_family[account_id]; billing_context = "managed_shared_billing"
            else:
                billing_family = payment; billing_context = "account_billing"
            rows.append({"account_id": account_id, "cycle_index": cycle_index, "cycle_start": cycle_start.date().isoformat(), "cycle_end": cycle_end.date().isoformat(), "plan": r.plan, "billing_status": r.billing_status, "entitlement_limit_per_active_day": plan_daily_units[str(r.plan)], "entitlement_contract_version": "synthetic-plan-contract-v1", "billing_family_ref": billing_family, "billing_context": billing_context, "managed_infrastructure": int(r.managed_infrastructure), "source_system": "synthetic_entitlement_ledger"})
        cycle_start = cycle_start + pd.Timedelta(days=cycle_days)
        cycle_index += 1
    ledger = pd.DataFrame(rows)
    ledger.to_csv(data / "entitlements.csv", index=False)
    return ledger


def evaluate_entitlement_abuse(data_dir: str | Path, out_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Evaluate cycle pressure while preserving legitimate shared-billing explanations."""
    data, out = Path(data_dir), Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    accounts = pd.read_csv(data / "accounts.csv", keep_default_na=False)
    telemetry = pd.read_csv(data / "telemetry.csv", keep_default_na=False)
    ledger = pd.read_csv(data / "entitlements.csv", keep_default_na=False)
    telemetry["timestamp"] = pd.to_datetime(telemetry.timestamp, utc=True, format="mixed")
    ledger["cycle_start"] = pd.to_datetime(ledger.cycle_start, utc=True); ledger["cycle_end"] = pd.to_datetime(ledger.cycle_end, utc=True)

    usage_rows = []
    for _, e in ledger.iterrows():
        mask = telemetry.account_id.eq(e.account_id) & telemetry.timestamp.dt.floor("D").between(e.cycle_start, e.cycle_end)
        w = telemetry.loc[mask]; active_days = int(w.timestamp.dt.date.nunique()) if len(w) else 0; requests = int(len(w))
        effective_allowance = int(e.entitlement_limit_per_active_day) * max(1, active_days); usage_ratio = requests / max(1, effective_allowance)
        usage_rows.append({"account_id": e.account_id, "cycle_index": int(e.cycle_index), "cycle_start": e.cycle_start.date().isoformat(), "cycle_end": e.cycle_end.date().isoformat(), "billing_family_ref": e.billing_family_ref, "billing_context": e.billing_context, "plan": e.plan, "managed_infrastructure": int(e.managed_infrastructure), "entitlement_contract_version": e.entitlement_contract_version, "requests": requests, "active_days": active_days, "effective_allowance": effective_allowance, "usage_ratio": usage_ratio, "near_limit": int(usage_ratio >= 0.85)})
    usage = pd.DataFrame(usage_rows).merge(accounts[["account_id", "ground_truth_abuse_type"]], on="account_id", how="left")

    family = usage.groupby(["cycle_index", "cycle_start", "cycle_end", "billing_family_ref"], as_index=False).agg(
        family_accounts=("account_id", "nunique"), combined_requests=("requests", "sum"), combined_allowance=("effective_allowance", "sum"), near_limit_accounts=("near_limit", "sum"), managed_share=("managed_infrastructure", "mean"), legitimate_shared_billing_accounts=("billing_context", lambda s: int((s == "managed_shared_billing").sum())), synthetic_linked_quota_accounts=("billing_context", lambda s: int((s == "synthetic_linked_billing_for_quota_evasion").sum())), benchmark_abuse_accounts=("ground_truth_abuse_type", lambda s: int((s != "legitimate").sum()))
    )
    family["family_usage_ratio"] = family.combined_requests / family.combined_allowance.clip(lower=1)
    family["shared_billing_context"] = ((family.family_accounts >= 2) & ((family.legitimate_shared_billing_accounts >= 2) | (family.managed_share >= 0.80))).astype(int)
    family["candidate_multi_account_evasion"] = ((family.family_accounts >= 2) & (family.near_limit_accounts >= 2) & (family.shared_billing_context == 0)).astype(int)
    family["reason_codes"] = np.where(family.candidate_multi_account_evasion.eq(1), "multi_account_same_billing_family|simultaneous_entitlement_pressure", np.where(family.shared_billing_context.eq(1), "shared_billing_requires_enterprise_context_review", "no_multi_account_pressure"))

    suspicious = family[family.candidate_multi_account_evasion.eq(1)].copy()
    queue = usage.merge(suspicious[["cycle_index", "billing_family_ref", "family_accounts", "near_limit_accounts", "family_usage_ratio", "reason_codes"]], on=["cycle_index", "billing_family_ref"], how="inner")
    if len(queue):
        queue["priority_score"] = (0.45 * queue.usage_ratio.clip(0, 1.5) + 0.20 * (queue.family_accounts.clip(1, 5) / 5) + 0.20 * (queue.near_limit_accounts.clip(1, 4) / 4) + 0.15 * queue.family_usage_ratio.clip(0, 1.5)).clip(0, 1)
        queue = queue.sort_values(["priority_score", "cycle_index"], ascending=[False, False])
    queue = queue[[c for c in ["account_id", "cycle_index", "cycle_start", "plan", "billing_family_ref", "usage_ratio", "family_accounts", "near_limit_accounts", "family_usage_ratio", "priority_score", "reason_codes"] if c in queue.columns]]

    required = {"account_id", "cycle_index", "cycle_start", "cycle_end", "entitlement_limit_per_active_day", "entitlement_contract_version", "billing_family_ref"}
    findings = [
        {"contract": "entitlement_schema", "status": "pass" if required.issubset(ledger.columns) else "fail", "severity": "info" if required.issubset(ledger.columns) else "critical", "observed": f"missing={sorted(required-set(ledger.columns))}", "recommended_action": "none" if required.issubset(ledger.columns) else "repair billing/entitlement integration before quota-abuse analysis"},
        {"contract": "entitlement_account_referential_integrity", "status": "pass" if ledger.account_id.isin(set(accounts.account_id)).all() else "fail", "severity": "info" if ledger.account_id.isin(set(accounts.account_id)).all() else "critical", "observed": f"orphan_rows={int((~ledger.account_id.isin(set(accounts.account_id))).sum())}", "recommended_action": "none" if ledger.account_id.isin(set(accounts.account_id)).all() else "repair account-key mapping"},
        {"contract": "entitlement_cycle_uniqueness", "status": "pass" if not ledger.duplicated(["account_id", "cycle_index"]).any() else "fail", "severity": "info" if not ledger.duplicated(["account_id", "cycle_index"]).any() else "critical", "observed": f"duplicate_account_cycles={int(ledger.duplicated(['account_id','cycle_index']).sum())}", "recommended_action": "none" if not ledger.duplicated(["account_id", "cycle_index"]).any() else "deduplicate or version entitlement events before analysis"},
    ]
    dq = pd.DataFrame(findings)
    usage.to_csv(out / "entitlement_cycle_usage.csv", index=False); family.to_csv(out / "billing_family_risk.csv", index=False); queue.to_csv(out / "entitlement_investigation_queue.csv", index=False); dq.to_csv(out / "entitlement_data_quality.csv", index=False)
    return usage, family, queue, dq
