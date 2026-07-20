from __future__ import annotations

from pathlib import Path
import hashlib
import pandas as pd


def _hash(prefix: str, value: str) -> str:
    return hashlib.sha256(f"{prefix}:{value}".encode()).hexdigest()[:16]


def inject_legitimate_entity_confounders(data_dir: str | Path, max_accounts: int = 12) -> None:
    """Inject approved organization contexts that resemble abuse linkage signals.

    These controls make shared token/payment/device evidence non-deterministic with respect to abuse labels.
    The context flag is retained for investigation but is intentionally excluded from model features.
    """
    data = Path(data_dir)
    accounts = pd.read_csv(data / "accounts.csv", keep_default_na=False)
    telemetry = pd.read_csv(data / "telemetry.csv", keep_default_na=False)

    eligible = accounts[(accounts.ground_truth_abuse_type.eq("legitimate")) & accounts.managed_infrastructure.eq(1)].account_id.tolist()
    selected = eligible[: min(max_accounts, len(eligible))]
    accounts["approved_organization_context"] = accounts.account_id.isin(selected).astype(int)

    for j, account_id in enumerate(selected):
        group = j // 3
        mask = telemetry.account_id.eq(account_id)
        telemetry.loc[mask, "payment_hash"] = _hash("payment", f"approved_org_billing_{group}")
        telemetry.loc[mask, "token_hash"] = _hash("token", f"approved_org_integration_{group}")
        # A shared managed runner is a legitimate device-link confounder, not identity proof.
        account_rows = telemetry.index[mask]
        if len(account_rows):
            runner_rows = account_rows[::4]
            telemetry.loc[runner_rows, "device_hash"] = _hash("device", f"approved_org_runner_{group}")

    accounts.to_csv(data / "accounts.csv", index=False)
    telemetry.to_csv(data / "telemetry.csv", index=False)
