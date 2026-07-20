from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd


def _rule_predictions(df: pd.DataFrame, velocity_cut: float, quota_cut: float) -> dict[str, pd.Series]:
    return {
        "identity_dispersion_multisignal": (df.unique_devices >= 5) & (df.unique_ips >= 7),
        "shared_token_multisignal": (df.max_token_degree >= 2) & ((df.risk_score >= 0.45) | (df.max_device_degree >= 2)),
        "scripted_usage_multisignal": (df.requests_per_active_day >= velocity_cut) & (df.cadence_regularity >= 0.48) & (df.overnight_share >= 0.07),
        "quota_evasion_multisignal": (df.quota_pressure >= quota_cut) & ((df.max_payment_degree >= 2) | (df.max_device_degree >= 2)),
        "policy_signal_escalation": (df.policy_signal_rate >= 0.03) | ((df.policy_signal_rate >= 0.015) & (df.injection_rate >= 0.015)),
    }


def _metrics(df: pd.DataFrame, pred: pd.Series) -> dict[str, float]:
    y = df.label.astype(int)
    p = pred.astype(bool)
    tp = int(((y == 1) & p).sum()); fp = int(((y == 0) & p).sum())
    tn = int(((y == 0) & ~p).sum()); fn = int(((y == 1) & ~p).sum())
    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "accounts_triggered": int(p.sum()),
        "precision": tp / max(1, tp + fp),
        "recall": tp / max(1, tp + fn),
        "false_positive_rate": fp / max(1, fp + tn),
        "review_workload_share": float(p.mean()),
    }


def _apply_adaptation(df: pd.DataFrame, strategy: str, strength: float) -> pd.DataFrame:
    out = df.copy()
    abuse = out.label.eq(1)
    strength = float(np.clip(strength, 0.0, 1.0))

    if strategy == "velocity_smoothing":
        out.loc[abuse, "requests_per_active_day"] *= 1.0 - 0.55 * strength
        out.loc[abuse, "cadence_regularity"] *= 1.0 - 0.65 * strength
        out.loc[abuse, "overnight_share"] *= 1.0 - 0.70 * strength
    elif strategy == "identity_fragmentation":
        out.loc[abuse, "unique_devices"] = np.maximum(1, np.floor(out.loc[abuse, "unique_devices"] * (1.0 - 0.60 * strength)))
        out.loc[abuse, "unique_ips"] = np.maximum(1, np.floor(out.loc[abuse, "unique_ips"] * (1.0 - 0.65 * strength)))
        out.loc[abuse, "max_device_degree"] = np.maximum(1, np.floor(out.loc[abuse, "max_device_degree"] * (1.0 - 0.60 * strength)))
    elif strategy == "token_rotation":
        out.loc[abuse, "max_token_degree"] = np.maximum(1, np.floor(out.loc[abuse, "max_token_degree"] * (1.0 - 0.85 * strength)))
        out.loc[abuse, "max_device_degree"] = np.maximum(1, np.floor(out.loc[abuse, "max_device_degree"] * (1.0 - 0.35 * strength)))
    elif strategy == "quota_spreading":
        out.loc[abuse, "quota_pressure"] *= 1.0 - 0.60 * strength
        out.loc[abuse, "max_payment_degree"] = np.maximum(1, np.floor(out.loc[abuse, "max_payment_degree"] * (1.0 - 0.65 * strength)))
        out.loc[abuse, "max_device_degree"] = np.maximum(1, np.floor(out.loc[abuse, "max_device_degree"] * (1.0 - 0.40 * strength)))
    elif strategy == "policy_signal_suppression":
        out.loc[abuse, "policy_signal_rate"] *= 1.0 - 0.75 * strength
        out.loc[abuse, "injection_rate"] *= 1.0 - 0.75 * strength
    elif strategy == "multi_signal_blending":
        out = _apply_adaptation(out, "velocity_smoothing", strength * 0.65)
        out = _apply_adaptation(out, "identity_fragmentation", strength * 0.55)
        out = _apply_adaptation(out, "token_rotation", strength * 0.55)
        out = _apply_adaptation(out, "quota_spreading", strength * 0.55)
        out = _apply_adaptation(out, "policy_signal_suppression", strength * 0.45)
    else:
        raise ValueError(f"unknown adaptation strategy: {strategy}")
    return out


def evaluate_adversarial_adaptation(scores: pd.DataFrame, out_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Stress-test frozen rules against coarse synthetic adaptive-adversary scenarios.

    This is an analytical resilience test, not a recipe for bypassing a real product control.
    """
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    holdout = scores.loc[scores.split.eq("holdout")].copy()
    development = scores.loc[scores.split.eq("train")].copy()
    velocity_cut = float(development.requests_per_active_day.quantile(0.75))
    quota_cut = float(development.quota_pressure.quantile(0.75))

    strategies = [
        "velocity_smoothing",
        "identity_fragmentation",
        "token_rotation",
        "quota_spreading",
        "policy_signal_suppression",
        "multi_signal_blending",
    ]
    strengths = [0.25, 0.50, 0.75, 1.00]
    baseline_preds = _rule_predictions(holdout, velocity_cut, quota_cut)
    baseline_metrics = {name: _metrics(holdout, pred) for name, pred in baseline_preds.items()}

    rows: list[dict] = []
    for strategy in strategies:
        for strength in strengths:
            adapted = _apply_adaptation(holdout, strategy, strength)
            preds = _rule_predictions(adapted, velocity_cut, quota_cut)
            for rule_name, pred in preds.items():
                m = _metrics(adapted, pred); base = baseline_metrics[rule_name]
                rows.append({
                    "strategy": strategy,
                    "adaptation_strength": strength,
                    "rule_name": rule_name,
                    "baseline_recall": base["recall"],
                    "adapted_recall": m["recall"],
                    "recall_drop": base["recall"] - m["recall"],
                    "baseline_precision": base["precision"],
                    "adapted_precision": m["precision"],
                    "baseline_fpr": base["false_positive_rate"],
                    "adapted_fpr": m["false_positive_rate"],
                    "adapted_accounts_triggered": m["accounts_triggered"],
                    "adapted_review_workload_share": m["review_workload_share"],
                    "simulation_boundary": "coarse synthetic stress test; not a real-product bypass procedure",
                })

    stress = pd.DataFrame(rows)
    stress.to_csv(out_dir / "adversarial_rule_stress.csv", index=False)

    defense_rows: list[dict] = []
    base_union = pd.concat(baseline_preds, axis=1).any(axis=1)
    base_union_metrics = _metrics(holdout, base_union)
    for strategy in strategies:
        for strength in strengths:
            adapted = _apply_adaptation(holdout, strategy, strength)
            preds = _rule_predictions(adapted, velocity_cut, quota_cut)
            union = pd.concat(preds, axis=1).any(axis=1)
            m = _metrics(adapted, union)
            defense_rows.append({
                "strategy": strategy,
                "adaptation_strength": strength,
                "defense": "multi_rule_union_diagnostic",
                "baseline_recall": base_union_metrics["recall"],
                "adapted_recall": m["recall"],
                "recall_drop": base_union_metrics["recall"] - m["recall"],
                "precision": m["precision"],
                "false_positive_rate": m["false_positive_rate"],
                "review_workload_share": m["review_workload_share"],
                "policy_boundary": "diagnostic only; requires human-review capacity and user-impact guardrails",
            })
    defense = pd.DataFrame(defense_rows)
    defense.to_csv(out_dir / "defense_in_depth_stress.csv", index=False)

    worst_single = stress.sort_values("recall_drop", ascending=False).iloc[0]
    worst_defense = defense.sort_values("recall_drop", ascending=False).iloc[0]
    summary = {
        "worst_single_rule": {
            "rule_name": str(worst_single.rule_name),
            "strategy": str(worst_single.strategy),
            "adaptation_strength": float(worst_single.adaptation_strength),
            "baseline_recall": float(worst_single.baseline_recall),
            "adapted_recall": float(worst_single.adapted_recall),
            "recall_drop": float(worst_single.recall_drop),
        },
        "worst_defense_in_depth": {
            "strategy": str(worst_defense.strategy),
            "adaptation_strength": float(worst_defense.adaptation_strength),
            "baseline_recall": float(worst_defense.baseline_recall),
            "adapted_recall": float(worst_defense.adapted_recall),
            "recall_drop": float(worst_defense.recall_drop),
        },
        "recommended_operating_response": "avoid dependence on one deterministic boundary; use independent signal families, shadow-canary-replay gates, and rollback when adaptation-sensitive recall proxies deteriorate",
        "automatic_enforcement_allowed": False,
    }
    (out_dir / "adversarial_stress_summary.json").write_text(json.dumps(summary, indent=2))
    return stress, defense, summary


def build_evasion_regression_gates(stress: pd.DataFrame, defense: pd.DataFrame, out_dir: str | Path) -> pd.DataFrame:
    max_single_drop = float(stress.recall_drop.max()) if len(stress) else 0.0
    max_defense_drop = float(defense.recall_drop.max()) if len(defense) else 0.0
    severe_defense = defense[defense.adaptation_strength >= 0.75] if len(defense) else defense
    min_severe_recall = float(severe_defense.adapted_recall.min()) if len(severe_defense) else 1.0
    rows = [
        {"gate":"single_rule_brittleness_visible","observed":max_single_drop,"guardrail":"must be measured, not hidden","status":"pass","action":"record largest recall degradation and identify brittle rule family"},
        {"gate":"defense_in_depth_not_worse_than_worst_single","observed":max_defense_drop,"guardrail":f"<= {max_single_drop:.4f}","status":"pass" if max_defense_drop <= max_single_drop + 1e-12 else "fail","action":"if failed, review correlated rule dependencies before promotion"},
        {"gate":"severe_adaptation_recall_floor","observed":min_severe_recall,"guardrail":">= 0.20 diagnostic floor","status":"pass" if min_severe_recall >= 0.20 else "warn","action":"if warning, keep affected controls in shadow/rework and add independent signals"},
    ]
    gates = pd.DataFrame(rows)
    gates.to_csv(Path(out_dir) / "evasion_regression_gates.csv", index=False)
    return gates
