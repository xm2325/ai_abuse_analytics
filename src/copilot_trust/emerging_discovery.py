from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


CHANGE_FEATURES = [
    "log_requests_delta",
    "token_rotation_delta",
    "surface_switch_delta",
    "surface_count_delta",
    "agent_share_delta",
    "acceptance_abs_delta",
]


def _robust_z(s: pd.Series) -> pd.Series:
    x = s.astype(float)
    med = float(x.median())
    mad = float((x - med).abs().median()) * 1.4826
    scale = mad if mad > 1e-8 else float(x.std(ddof=0))
    scale = scale if scale > 1e-8 else 1.0
    return (x - med) / scale


def _daily_behavior(telemetry: pd.DataFrame) -> pd.DataFrame:
    t = telemetry.copy().sort_values(["account_id", "timestamp"])
    t["event_date"] = t.timestamp.dt.floor("D")
    t["previous_surface"] = t.groupby(["account_id", "event_date"]).model_family.shift()
    t["surface_switch"] = ((t.previous_surface.notna()) & (t.model_family != t.previous_surface)).astype(int)
    t["agent_event"] = t.model_family.eq("agent").astype(int)
    daily = t.groupby(["account_id", "event_date"], as_index=False).agg(
        requests=("request_id", "count"),
        unique_tokens=("token_hash", lambda s: int(s[s.ne("")].nunique())),
        unique_surfaces=("model_family", "nunique"),
        surface_switch_rate=("surface_switch", "mean"),
        agent_share=("agent_event", "mean"),
        acceptance_rate=("completion_accepted", "mean"),
        unique_devices=("device_hash", lambda s: int(s[s.ne("")].nunique())),
        unique_ips=("ip_hash", lambda s: int(s[s.ne("")].nunique())),
    )
    return daily


def _aggregate_windows(daily: pd.DataFrame, accounts: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp, pd.Timestamp]:
    max_day = daily.event_date.max()
    recent_start = max_day - pd.Timedelta(days=9)
    baseline_start = recent_start - pd.Timedelta(days=28)
    baseline = daily[(daily.event_date >= baseline_start) & (daily.event_date < recent_start)]
    recent = daily[daily.event_date >= recent_start]
    metrics = ["requests", "unique_tokens", "unique_surfaces", "surface_switch_rate", "agent_share", "acceptance_rate", "unique_devices", "unique_ips"]
    b = baseline.groupby("account_id")[metrics].mean().add_prefix("baseline_")
    r = recent.groupby("account_id")[metrics].mean().add_prefix("recent_")
    x = accounts[[c for c in ["account_id", "plan", "region", "managed_infrastructure", "legitimate_profile", "approved_organization_context"] if c in accounts.columns]].copy()
    x = x.merge(b, left_on="account_id", right_index=True, how="left").merge(r, left_on="account_id", right_index=True, how="left")
    numeric = [c for c in x.columns if c.startswith("baseline_") or c.startswith("recent_")]
    x[numeric] = x[numeric].fillna(0.0)
    x["log_requests_delta"] = np.log1p(x.recent_requests) - np.log1p(x.baseline_requests)
    x["token_rotation_delta"] = x.recent_unique_tokens - x.baseline_unique_tokens
    x["surface_switch_delta"] = x.recent_surface_switch_rate - x.baseline_surface_switch_rate
    x["surface_count_delta"] = x.recent_unique_surfaces - x.baseline_unique_surfaces
    x["agent_share_delta"] = x.recent_agent_share - x.baseline_agent_share
    x["acceptance_abs_delta"] = (x.recent_acceptance_rate - x.baseline_acceptance_rate).abs()
    for c in CHANGE_FEATURES:
        x[f"z_{c}"] = _robust_z(x[c])
    positive = ["log_requests_delta", "token_rotation_delta", "surface_switch_delta", "surface_count_delta", "agent_share_delta"]
    z2 = sum(np.maximum(x[f"z_{c}"], 0.0) ** 2 for c in positive)
    z2 += 0.25 * x["z_acceptance_abs_delta"].abs() ** 2
    x["novelty_score"] = np.sqrt(z2)
    return x, recent_start, max_day


def _incident_diagnostics(telemetry: pd.DataFrame, recent_start: pd.Timestamp, out: Path) -> pd.DataFrame:
    t = telemetry.copy()
    baseline = t[t.timestamp < recent_start]
    recent = t[t.timestamp >= recent_start]
    rows = []
    for signal in ["ip_hash", "device_hash"]:
        b = float(baseline[signal].eq("").mean()) if len(baseline) else 0.0
        r = float(recent[signal].eq("").mean()) if len(recent) else 0.0
        worsening = max(0.0, r - b)
        rows.append({
            "signal": signal,
            "baseline_missing_rate": b,
            "recent_missing_rate": r,
            "worsening_percentage_points": 100 * worsening,
            "status": "possible_data_incident" if worsening >= 0.08 else "coverage_stable_for_novelty_review",
        })
    d = pd.DataFrame(rows)
    d.to_csv(out / "novelty_incident_diagnostics.csv", index=False)
    return d


def _cluster_candidates(candidates: pd.DataFrame, seed: int) -> pd.DataFrame:
    c = candidates.copy()
    if len(c) == 0:
        c["cohort_id"] = pd.Series(dtype=str)
        return c
    k = min(3, max(1, len(c) // 4))
    if k == 1:
        c["cohort_id"] = "N-001"
        return c
    X = StandardScaler().fit_transform(c[CHANGE_FEATURES].fillna(0.0))
    labels = KMeans(n_clusters=k, random_state=seed, n_init=20).fit_predict(X)
    c["cohort_id"] = [f"N-{int(v)+1:03d}" for v in labels]
    return c


def _cohort_name(row: pd.Series) -> str:
    if row.mean_token_rotation_delta >= 1.5 and row.mean_surface_switch_delta >= 0.20:
        return "candidate_surface_rotation_token_churn"
    if row.mean_agent_share_delta >= 0.20 and row.mean_surface_count_delta >= 0.50:
        return "candidate_agent_surface_shift"
    if row.mean_log_requests_delta >= 0.50:
        return "candidate_behavioral_volume_shift"
    return "candidate_multivariate_behavior_shift"


def _cohort_summaries(candidates: pd.DataFrame, incident_clear: bool, out: Path) -> pd.DataFrame:
    rows = []
    for cohort_id, g in candidates.groupby("cohort_id"):
        row = {
            "cohort_id": cohort_id,
            "candidate_accounts": int(len(g)),
            "mean_novelty_score": float(g.novelty_score.mean()),
            "mean_log_requests_delta": float(g.log_requests_delta.mean()),
            "mean_token_rotation_delta": float(g.token_rotation_delta.mean()),
            "mean_surface_switch_delta": float(g.surface_switch_delta.mean()),
            "mean_surface_count_delta": float(g.surface_count_delta.mean()),
            "mean_agent_share_delta": float(g.agent_share_delta.mean()),
            "known_detection_flag_rate": float(g.known_detection_flagged.mean()) if "known_detection_flagged" in g else 0.0,
            "approved_org_context_share": float(g.approved_organization_context.mean()) if "approved_organization_context" in g else 0.0,
            "data_incident_screen": "clear" if incident_clear else "review_telemetry_incident_first",
        }
        row["candidate_taxonomy_name"] = _cohort_name(pd.Series(row))
        rows.append(row)
    summary = pd.DataFrame(rows).sort_values("mean_novelty_score", ascending=False) if rows else pd.DataFrame(columns=["cohort_id", "candidate_accounts", "candidate_taxonomy_name"])
    summary.to_csv(out / "emerging_behavior_cohorts.csv", index=False)
    return summary


def _graph_triage(candidates: pd.DataFrame, telemetry: pd.DataFrame, accounts: pd.DataFrame, out: Path) -> pd.DataFrame:
    ids = set(candidates.account_id)
    parent = {a: a for a in ids}

    def find(a: str) -> str:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    edge_rows = []
    for entity, strength in [("token_hash", "strong"), ("payment_hash", "strong"), ("device_hash", "strong"), ("ip_hash", "context_only")]:
        for value, g in telemetry[telemetry[entity].ne("")].groupby(entity):
            members = sorted(ids.intersection(set(g.account_id)))
            if len(members) < 2 or len(members) > 8:
                continue
            for a, b in combinations(members, 2):
                edge_rows.append({"account_a": a, "account_b": b, "entity_type": entity, "entity_degree_in_candidate_set": len(members), "evidence_strength": strength})
                if strength == "strong":
                    union(a, b)
    edges = pd.DataFrame(edge_rows)
    if len(edges):
        edges.to_csv(out / "emerging_graph_edges.csv", index=False)
    else:
        pd.DataFrame(columns=["account_a", "account_b", "entity_type", "entity_degree_in_candidate_set", "evidence_strength"]).to_csv(out / "emerging_graph_edges.csv", index=False)

    context_cols = [c for c in ["account_id", "managed_infrastructure", "approved_organization_context"] if c in accounts]
    context = accounts[context_cols].copy()
    rows = []
    for root in sorted({find(a) for a in ids}):
        members = sorted([a for a in ids if find(a) == root])
        es = edges[(edges.account_a.isin(members)) & (edges.account_b.isin(members))] if len(edges) else pd.DataFrame()
        ctx = context[context.account_id.isin(members)]
        approved_share = float(ctx.approved_organization_context.mean()) if "approved_organization_context" in ctx and len(ctx) else 0.0
        managed_share = float(ctx.managed_infrastructure.mean()) if "managed_infrastructure" in ctx and len(ctx) else 0.0
        strong_edges = int((es.evidence_strength == "strong").sum()) if len(es) else 0
        ip_edges = int((es.entity_type == "ip_hash").sum()) if len(es) else 0
        if approved_share >= 0.5:
            interpretation = "approved_organization_context_requires_benign_explanation_review"
        elif strong_edges > 0:
            interpretation = "strong_entity_linkage_requires_investigation"
        else:
            interpretation = "behavioral_cohort_without_strong_identity_linkage"
        rows.append({
            "community_id": f"G-{len(rows)+1:03d}",
            "accounts": "|".join(members),
            "community_size": len(members),
            "strong_entity_edges": strong_edges,
            "ip_context_edges": ip_edges,
            "managed_share": managed_share,
            "approved_org_context_share": approved_share,
            "interpretation": interpretation,
            "identity_boundary": "IP-only overlap never proves common control",
        })
    communities = pd.DataFrame(rows)
    communities.to_csv(out / "emerging_graph_triage.csv", index=False)
    return communities


def _taxonomy_and_shadow(summary: pd.DataFrame, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    taxonomy_rows = []
    shadow_rows = []
    for _, r in summary.iterrows():
        evidence = []
        if r.mean_token_rotation_delta >= 1.0: evidence.append("token_rotation_shift")
        if r.mean_surface_switch_delta >= 0.15: evidence.append("surface_switch_shift")
        if r.mean_surface_count_delta >= 0.4: evidence.append("surface_mix_expansion")
        if r.mean_agent_share_delta >= 0.15: evidence.append("agent_share_shift")
        if r.mean_log_requests_delta >= 0.4: evidence.append("request_volume_shift")
        evidence_text = "|".join(evidence) if evidence else "multivariate_novelty"
        taxonomy_rows.append({
            "candidate_taxonomy_id": f"TAX-{len(taxonomy_rows)+1:03d}",
            "cohort_id": r.cohort_id,
            "candidate_name": r.candidate_taxonomy_name,
            "evidence_summary": evidence_text,
            "known_detection_flag_rate": r.known_detection_flag_rate,
            "data_incident_screen": r.data_incident_screen,
            "competing_explanations": "approved integration|product rollout|client retry behavior|SDK change|enterprise automation|telemetry change",
            "status": "analyst_taxonomy_review_required",
            "policy_boundary": "candidate taxonomy only; not an abuse finding",
        })
        shadow_rows.append({
            "candidate_rule_id": f"NOVEL-R-{len(shadow_rows)+1:03d}",
            "cohort_id": r.cohort_id,
            "candidate_name": r.candidate_taxonomy_name,
            "development_only_predicate": "recent token rotation + surface switching + surface-mix expansion above cohort-derived development thresholds",
            "next_stage": "independent_shadow_replay_required",
            "required_evidence": "independent time window + matured review labels + FPR uncertainty + legitimate integration review + queue capacity",
            "automatic_enforcement_allowed": False,
        })
    taxonomy = pd.DataFrame(taxonomy_rows)
    shadow = pd.DataFrame(shadow_rows)
    taxonomy.to_csv(out / "candidate_taxonomy_proposals.csv", index=False)
    shadow.to_csv(out / "novel_shadow_rule_candidates.csv", index=False)
    return taxonomy, shadow


def discover_emerging_abuse(data_dir: str | Path, out_dir: str | Path, scores: pd.DataFrame, seed: int = 17) -> dict[str, object]:
    """Discover behavior cohorts without using the hidden benchmark taxonomy or ground-truth labels."""
    data, out = Path(data_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    accounts = pd.read_csv(data / "accounts.csv", keep_default_na=False)
    telemetry = pd.read_csv(data / "telemetry.csv", keep_default_na=False)
    telemetry["timestamp"] = pd.to_datetime(telemetry.timestamp, utc=True, format="mixed")

    daily = _daily_behavior(telemetry)
    features, recent_start, max_day = _aggregate_windows(daily, accounts)
    diagnostics = _incident_diagnostics(telemetry, recent_start, out)
    incident_clear = not diagnostics.status.eq("possible_data_incident").any()

    known = scores[[c for c in ["account_id", "flagged", "risk_score", "reason_codes"] if c in scores]].copy()
    known = known.rename(columns={"flagged": "known_detection_flagged", "risk_score": "known_risk_score", "reason_codes": "known_reason_codes"})
    features = features.merge(known, on="account_id", how="left")
    features["known_detection_flagged"] = features.known_detection_flagged.fillna(0).astype(int)

    candidate_n = min(len(features), max(6, int(np.ceil(0.12 * len(features)))))
    candidates = features.sort_values("novelty_score", ascending=False).head(candidate_n).copy()
    candidates = _cluster_candidates(candidates, seed)
    candidates["triage_status"] = np.where(incident_clear, "behavioral_novelty_candidate", "hold_for_data_incident_review")
    candidates["enforcement_boundary"] = "human investigation only; novelty is not proof of abuse"
    candidates.to_csv(out / "emerging_novelty_accounts.csv", index=False)

    summary = _cohort_summaries(candidates, incident_clear, out)
    communities = _graph_triage(candidates, telemetry, accounts, out)
    taxonomy, shadow = _taxonomy_and_shadow(summary, out)

    # Benchmark-only evaluation is deliberately calculated after discovery and never fed back into ranking.
    benchmark = {"hidden_manifest_present": False, "hidden_accounts": 0, "hidden_accounts_discovered": 0, "candidate_set_size": int(len(candidates)), "hidden_recall_at_candidate_set": None, "candidate_precision_for_hidden_pattern": None}
    manifest_path = data / "hidden_novelty_manifest.csv"
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)
        hidden = set(manifest.account_id)
        discovered = hidden.intersection(set(candidates.account_id))
        benchmark = {
            "hidden_manifest_present": True,
            "hidden_accounts": len(hidden),
            "hidden_accounts_discovered": len(discovered),
            "candidate_set_size": int(len(candidates)),
            "hidden_recall_at_candidate_set": len(discovered) / max(1, len(hidden)),
            "candidate_precision_for_hidden_pattern": len(discovered) / max(1, len(candidates)),
            "benchmark_only_label_boundary": "hidden manifest is never used by discovery, clustering, graph triage, or taxonomy generation",
        }
    (out / "emerging_discovery_benchmark.json").write_text(json.dumps(benchmark, indent=2))

    return {
        "accounts": candidates,
        "cohorts": summary,
        "communities": communities,
        "taxonomy": taxonomy,
        "shadow_rules": shadow,
        "diagnostics": diagnostics,
        "benchmark": benchmark,
        "recent_start": recent_start,
        "max_day": max_day,
    }
