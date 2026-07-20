from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

FEATURES = [
    "requests_per_active_day", "unique_devices", "unique_ips", "acceptance_rate",
    "injection_rate", "policy_signal_rate", "overnight_share", "quota_pressure",
    "cadence_regularity", "max_token_degree", "max_device_degree",
]


def _psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    ref = pd.to_numeric(reference, errors="coerce").dropna().to_numpy()
    cur = pd.to_numeric(current, errors="coerce").dropna().to_numpy()
    if len(ref) < 10 or len(cur) < 10:
        return float("nan")
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    r, _ = np.histogram(ref, bins=edges)
    c, _ = np.histogram(cur, bins=edges)
    r = np.clip(r / max(1, r.sum()), 1e-6, None)
    c = np.clip(c / max(1, c.sum()), 1e-6, None)
    return float(np.sum((c - r) * np.log(c / r)))


def evaluate_drift(scores: pd.DataFrame, out_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare development and holdout populations and check score calibration by risk decile.

    This is diagnostic monitoring, not a claim that a synthetic holdout represents temporal production drift.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    reference = scores[scores.split.eq("train")]
    current = scores[scores.split.eq("holdout")]
    rows = []
    for f in FEATURES:
        psi = _psi(reference[f], current[f])
        if np.isnan(psi):
            status = "insufficient_data"
        elif psi >= 0.25:
            status = "investigate"
        elif psi >= 0.10:
            status = "watch"
        else:
            status = "stable"
        rows.append({
            "feature": f,
            "reference_mean": float(reference[f].mean()),
            "current_mean": float(current[f].mean()),
            "psi": psi,
            "status": status,
            "interpretation": "population-shift diagnostic; validate instrumentation and segment mix before model changes",
        })
    drift = pd.DataFrame(rows).sort_values(["status", "psi"], ascending=[True, False])
    drift.to_csv(out / "feature_drift_diagnostics.csv", index=False)

    h = current.copy()
    try:
        h["risk_bin"] = pd.qcut(h.risk_score, q=min(10, max(2, h.risk_score.nunique())), duplicates="drop")
    except ValueError:
        h["risk_bin"] = "all"
    calib = h.groupby("risk_bin", observed=False).agg(
        n=("account_id", "size"),
        mean_predicted_risk=("risk_score", "mean"),
        observed_known_abuse_rate=("label", "mean"),
        flagged_rate=("flagged", "mean"),
    ).reset_index()
    calib["absolute_calibration_gap"] = (calib.mean_predicted_risk - calib.observed_known_abuse_rate).abs()
    calib["risk_bin"] = calib.risk_bin.astype(str)
    calib.to_csv(out / "risk_calibration_bins.csv", index=False)
    return drift, calib
