from __future__ import annotations

from pathlib import Path
import hashlib
import numpy as np
import pandas as pd


def _hash(prefix: str, value: str) -> str:
    return hashlib.sha256(f"{prefix}:{value}".encode()).hexdigest()[:16]


def inject_hidden_emerging_pattern(data_dir: str | Path, seed: int = 17) -> pd.DataFrame:
    """Inject a benchmark-only late emerging pattern that is absent from the known taxonomy.

    The detector never reads the hidden manifest. The pattern is deliberately designed to avoid
    existing rule shortcuts: modest request growth, no policy-signal spike, no cross-account token
    sharing, stable device/IP identity, but abrupt surface switching plus per-account token churn.
    """
    data = Path(data_dir)
    accounts = pd.read_csv(data / "accounts.csv", keep_default_na=False)
    telemetry = pd.read_csv(data / "telemetry.csv", keep_default_na=False)
    telemetry["timestamp"] = pd.to_datetime(telemetry.timestamp, utc=True, format="mixed")
    rng = np.random.default_rng(seed + 707)

    if "approved_organization_context" not in accounts:
        accounts["approved_organization_context"] = 0

    eligible = accounts[
        accounts.ground_truth_abuse_type.eq("legitimate")
        & accounts.legitimate_profile.eq("standard")
        & accounts.approved_organization_context.astype(int).eq(0)
        & accounts.plan.isin(["individual", "free"])
    ].copy()
    if len(eligible) < 3:
        eligible = accounts[accounts.ground_truth_abuse_type.eq("legitimate")].copy()

    n_hidden = min(6, max(3, int(round(len(accounts) * 0.03))))
    n_hidden = min(n_hidden, len(eligible))
    if n_hidden == 0:
        manifest = pd.DataFrame(columns=["account_id", "hidden_pattern", "campaign_start", "taxonomy_visible_to_detector"])
        manifest.to_csv(data / "hidden_novelty_manifest.csv", index=False)
        return manifest

    counts = telemetry.groupby("account_id").size().rename("events")
    eligible["events"] = eligible.account_id.map(counts).fillna(0)
    pool = eligible.sort_values("events", ascending=False).head(max(n_hidden * 4, n_hidden))
    selected = pool.sample(n=n_hidden, random_state=seed + 707).account_id.tolist()

    max_day = telemetry.timestamp.max().floor("D")
    campaign_start = max_day - pd.Timedelta(days=7)
    next_id = len(telemetry)
    new_rows: list[dict] = []

    for account_id in selected:
        acct = accounts.loc[accounts.account_id.eq(account_id)].iloc[0]
        history = telemetry.loc[telemetry.account_id.eq(account_id)].sort_values("timestamp")
        if len(history):
            base_device = history.loc[history.device_hash.ne(""), "device_hash"].iloc[0] if history.device_hash.ne("").any() else _hash("device", account_id)
            base_ip = history.loc[history.ip_hash.ne(""), "ip_hash"].iloc[0] if history.ip_hash.ne("").any() else _hash("ip", account_id)
            base_payment = history.loc[history.payment_hash.ne(""), "payment_hash"].iloc[0] if history.payment_hash.ne("").any() else _hash("payment", account_id)
            entitlement = int(history.entitlement_limit.max())
        else:
            base_device = _hash("device", account_id); base_ip = _hash("ip", account_id); base_payment = _hash("payment", account_id)
            entitlement = {"free": 50, "individual": 300, "business": 600, "enterprise": 900}[acct.plan]

        for day_offset in range(8):
            day = campaign_start + pd.Timedelta(days=day_offset)
            n = int(rng.integers(7, 11))
            burst_anchors = [9 * 3600 + int(rng.integers(0, 1200)), 16 * 3600 + int(rng.integers(0, 1200))]
            for j in range(n):
                anchor = burst_anchors[j % 2]
                seconds = anchor + (j // 2) * int(rng.integers(55, 150))
                ts = day + pd.Timedelta(seconds=seconds)
                model_family = ["code_completion", "agent", "chat"][j % 3]
                token_hash = _hash("novel-rotating-token", f"{account_id}:{day_offset}:{j % 4}")
                new_rows.append({
                    "request_id": f"req_{next_id:09d}",
                    "timestamp": ts,
                    "account_id": account_id,
                    "device_hash": base_device,
                    "ip_hash": base_ip,
                    "payment_hash": base_payment,
                    "token_hash": token_hash,
                    "model_family": model_family,
                    "prompt_chars": int(np.clip(rng.lognormal(5.0, 0.55), 20, 7000)),
                    "completion_chars": int(np.clip(rng.lognormal(4.8, 0.55), 10, 6000)),
                    "completion_accepted": int(rng.random() < 0.55),
                    "prompt_injection_signal": 0,
                    "content_policy_signal": 0,
                    "safety_blocked": 0,
                    "entitlement_limit": entitlement,
                })
                next_id += 1

    augmented = pd.concat([telemetry, pd.DataFrame(new_rows)], ignore_index=True)
    augmented["timestamp"] = pd.to_datetime(augmented.timestamp, utc=True, format="mixed")
    augmented = augmented.sort_values("timestamp").reset_index(drop=True)
    augmented.to_csv(data / "telemetry.csv", index=False)

    manifest = pd.DataFrame({
        "account_id": selected,
        "hidden_pattern": "surface_hopping_token_rotation",
        "campaign_start": campaign_start.date().isoformat(),
        "taxonomy_visible_to_detector": 0,
    })
    manifest.to_csv(data / "hidden_novelty_manifest.csv", index=False)
    return manifest
