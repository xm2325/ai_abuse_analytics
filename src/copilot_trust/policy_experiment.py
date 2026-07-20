from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd


ROLLOUT = pd.Timestamp("2026-05-06", tz="UTC")
ARMS = ("control", "shadow", "canary")


def _stable_unit(value: str) -> float:
    h = hashlib.sha256(value.encode()).hexdigest()[:12]
    return int(h, 16) / float(16**12 - 1)


class _UnionFind:
    def __init__(self, items: list[str]):
        self.parent = {x: x for x in items}

    def find(self, x: str) -> str:
        p = self.parent[x]
        if p != x:
            self.parent[x] = self.find(p)
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def _build_preperiod_assignment(accounts: pd.DataFrame, telemetry: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    pre = telemetry[telemetry.timestamp < ROLLOUT].copy()
    pre["event_date"] = pre.timestamp.dt.floor("D")
    agg = pre.groupby("account_id").agg(
        pre_requests=("request_id", "size"),
        pre_active_days=("event_date", "nunique"),
        pre_policy_signals=("content_policy_signal", "sum"),
    ).reset_index()
    agg["pre_requests_per_active_day"] = agg.pre_requests / agg.pre_active_days.clip(lower=1)
    agg["pre_policy_signal_rate"] = agg.pre_policy_signals / agg.pre_requests.clip(lower=1)
    meta = accounts[["account_id", "plan", "region", "org_id", "managed_infrastructure"]].copy()
    base = meta.merge(agg, on="account_id", how="left").fillna({"pre_requests": 0, "pre_active_days": 0, "pre_policy_signals": 0, "pre_requests_per_active_day": 0, "pre_policy_signal_rate": 0})
    med = float(base.loc[base.pre_active_days >= 5, "pre_requests_per_active_day"].median()) if (base.pre_active_days >= 5).any() else 0.0
    base["eligible"] = ((base.pre_active_days >= 5) & ((base.pre_requests_per_active_day >= med) | (base.pre_policy_signal_rate >= 0.01))).astype(int)
    eligible_ids = base.loc[base.eligible.eq(1), "account_id"].tolist()
    uf = _UnionFind(eligible_ids)

    # Organization membership and low-degree token/payment reuse define randomization clusters.
    orgs = base[base.eligible.eq(1) & base.org_id.fillna("").ne("")].groupby("org_id").account_id.apply(list)
    for members in orgs:
        for x in members[1:]:
            uf.union(members[0], x)
    pre_e = pre[pre.account_id.isin(eligible_ids)]
    for col in ["token_hash", "payment_hash"]:
        for _, members in pre_e[pre_e[col].fillna("").ne("")].groupby(col).account_id.unique().items():
            members = list(members)
            if 2 <= len(members) <= 6:
                for x in members[1:]:
                    uf.union(members[0], x)

    base["cluster_id"] = base.account_id.map(lambda x: f"cl_{uf.find(x)}" if x in uf.parent else f"ineligible_{x}")
    eligible = base[base.eligible.eq(1)].copy()
    clusters = eligible.groupby("cluster_id").agg(
        cluster_accounts=("account_id", "nunique"),
        pre_requests_per_active_day=("pre_requests_per_active_day", "mean"),
        pre_policy_signal_rate=("pre_policy_signal_rate", "mean"),
    ).reset_index()
    clusters["strat_score"] = np.log1p(clusters.pre_requests_per_active_day) + 4.0 * clusters.pre_policy_signal_rate
    if len(clusters) >= 3:
        clusters["stratum"] = pd.qcut(clusters.strat_score.rank(method="first"), q=min(3, len(clusters)), labels=False, duplicates="drop").astype(str)
    else:
        clusters["stratum"] = "0"
    rng = np.random.default_rng(seed)
    arm_pattern = np.array(["control", "canary", "shadow", "control", "canary", "shadow", "control", "control", "canary", "shadow"], dtype=object)
    arm_map: dict[str, str] = {}
    for _, g in clusters.groupby("stratum"):
        ids = g.cluster_id.to_numpy().copy(); rng.shuffle(ids)
        for j, cid in enumerate(ids):
            arm_map[str(cid)] = str(arm_pattern[j % len(arm_pattern)])
    clusters["arm"] = clusters.cluster_id.map(arm_map)
    clusters["cluster_exposed"] = clusters.apply(lambda r: int(r.arm == "canary" and _stable_unit(f"exposure:{seed}:{r.cluster_id}") < 0.82), axis=1)
    assignment = eligible.merge(clusters[["cluster_id", "stratum", "arm", "cluster_exposed"]], on="cluster_id", how="left")
    assignment["assigned_canary"] = assignment.arm.eq("canary").astype(int)
    assignment["exposed"] = assignment.cluster_exposed.astype(int)

    # Weak IP-context neighborhoods are not used to define identity or randomization clusters.
    ip_pairs = []
    for ip, members in pre_e[pre_e.ip_hash.fillna("").ne("")].groupby("ip_hash").account_id.unique().items():
        members = sorted(set(members))
        if 2 <= len(members) <= 10:
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    ip_pairs.append((members[i], members[j], ip))
    ip_edges = pd.DataFrame(ip_pairs, columns=["account_a", "account_b", "ip_context_hash"]) if ip_pairs else pd.DataFrame(columns=["account_a", "account_b", "ip_context_hash"])
    arm_by_account = assignment.set_index("account_id").arm.to_dict()
    if len(ip_edges):
        ip_edges["arm_a"] = ip_edges.account_a.map(arm_by_account); ip_edges["arm_b"] = ip_edges.account_b.map(arm_by_account)
        ip_edges = ip_edges.dropna(subset=["arm_a", "arm_b"])
        ip_edges["cross_arm"] = ip_edges.arm_a.ne(ip_edges.arm_b).astype(int)
    return assignment, ip_edges


def _daily_panel(telemetry: pd.DataFrame, assignment: pd.DataFrame) -> pd.DataFrame:
    t = telemetry[telemetry.account_id.isin(assignment.account_id)].copy()
    t["event_date"] = t.timestamp.dt.floor("D")
    t["is_primary"] = t.model_family.eq("code_completion").astype(int)
    t["is_alt"] = t.model_family.isin(["chat", "agent"]).astype(int)
    daily = t.groupby(["account_id", "event_date"]).agg(
        raw_requests=("request_id", "size"),
        raw_primary_requests=("is_primary", "sum"),
        raw_alt_requests=("is_alt", "sum"),
        accepted=("completion_accepted", "sum"),
        prompt_chars_mean=("prompt_chars", "mean"),
    ).reset_index()
    dates = pd.date_range(t.event_date.min(), t.event_date.max(), freq="D", tz="UTC")
    idx = pd.MultiIndex.from_product([assignment.account_id, dates], names=["account_id", "event_date"])
    daily = daily.set_index(["account_id", "event_date"]).reindex(idx).reset_index()
    for c in ["raw_requests", "raw_primary_requests", "raw_alt_requests", "accepted"]:
        daily[c] = daily[c].fillna(0.0).astype(float)
    # Negative-control outcome: carry an account's observed pre-period mean prompt length across zero-request days.
    prompt_baseline = t[t.timestamp < ROLLOUT].groupby("account_id").prompt_chars.mean().to_dict()
    daily["prompt_chars_mean"] = daily.apply(lambda r: float(r.prompt_chars_mean) if pd.notna(r.prompt_chars_mean) else float(prompt_baseline.get(r.account_id, 0.0)), axis=1)
    daily = daily.merge(assignment[["account_id", "cluster_id", "arm", "exposed", "plan", "region", "managed_infrastructure"]], on="account_id", how="left")
    daily["post"] = (daily.event_date >= ROLLOUT).astype(int)
    return daily


def _inject_hidden_policy_effect(panel: pd.DataFrame, accounts: pd.DataFrame, ip_edges: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    gt = accounts.set_index("account_id").ground_truth_abuse_type.to_dict()
    out = panel.copy()
    out["primary_requests"] = out.raw_primary_requests.astype(float)
    out["alternate_surface_requests"] = out.raw_alt_requests.astype(float)
    out["acceptance_rate"] = out.accepted / out.raw_requests.clip(lower=1)
    out["migration_inflow"] = 0.0
    responsive_types = {"scripted_automation": 0.45, "quota_evasion": 0.35}
    assignment = out[["account_id", "arm", "exposed", "region"]].drop_duplicates().set_index("account_id")

    neighbor_map: dict[str, list[str]] = {}
    if len(ip_edges):
        for _, r in ip_edges.iterrows():
            neighbor_map.setdefault(r.account_a, []).append(r.account_b)
            neighbor_map.setdefault(r.account_b, []).append(r.account_a)
    manifest_rows = []
    migration_targets: dict[str, str | None] = {}
    for acc in assignment.index:
        kind = str(gt.get(acc, "legitimate")); direct = responsive_types.get(kind, 0.0)
        is_responder = int(direct > 0)
        canary_exposed = int(assignment.loc[acc, "arm"] == "canary" and assignment.loc[acc, "exposed"] == 1)
        migration_prop = 0.20 if (is_responder and _stable_unit(f"migration:{seed}:{acc}") < 0.55) else 0.0
        target = None
        if migration_prop > 0 and canary_exposed:
            candidates = [x for x in neighbor_map.get(acc, []) if x in assignment.index and assignment.loc[x, "arm"] != "canary"]
            if not candidates:
                same_region = assignment[(assignment.region == assignment.loc[acc, "region"]) & (assignment.arm != "canary")].index.tolist()
                candidates = same_region
            if candidates:
                target = sorted(candidates)[int(_stable_unit(f"target:{seed}:{acc}") * len(candidates)) % len(candidates)]
        migration_targets[acc] = target
        manifest_rows.append({
            "account_id": acc,
            "hidden_responder_type": kind if is_responder else "non_responder",
            "true_responder": is_responder,
            "injected_primary_fraction_reduction": direct if canary_exposed else 0.0,
            "injected_alt_displacement_fraction": 0.35 if (is_responder and canary_exposed) else 0.0,
            "injected_neighbor_migration_fraction": migration_prop if canary_exposed else 0.0,
            "migration_target_account": target or "",
            "manifest_boundary": "benchmark only; never used by assignment or effect estimation",
        })

    migration_additions: list[tuple[str, pd.Timestamp, float]] = []
    for acc, target in migration_targets.items():
        mask = out.account_id.eq(acc) & out.post.eq(1) & out.arm.eq("canary") & out.exposed.eq(1)
        if not mask.any():
            continue
        kind = str(gt.get(acc, "legitimate")); direct = responsive_types.get(kind, 0.0)
        if direct > 0:
            original = out.loc[mask, "primary_requests"].copy()
            removed = original * direct
            out.loc[mask, "primary_requests"] = original - removed
            out.loc[mask, "alternate_surface_requests"] += removed * 0.35
            # Small generic friction is visible in an operational acceptance-rate guardrail.
            out.loc[mask, "acceptance_rate"] = (out.loc[mask, "acceptance_rate"] - 0.008).clip(lower=0)
            if target:
                for date, amount in zip(out.loc[mask, "event_date"], removed * 0.20):
                    migration_additions.append((target, date, float(amount)))
        else:
            # Legitimate/non-responsive canary accounts experience only a mild friction effect.
            out.loc[mask, "primary_requests"] *= 0.98
            out.loc[mask, "acceptance_rate"] = (out.loc[mask, "acceptance_rate"] - 0.006).clip(lower=0)

    if migration_additions:
        add = pd.DataFrame(migration_additions, columns=["account_id", "event_date", "migration_inflow"])
        add = add.groupby(["account_id", "event_date"], as_index=False).migration_inflow.sum()
        out = out.drop(columns="migration_inflow").merge(add, on=["account_id", "event_date"], how="left")
        out["migration_inflow"] = out.migration_inflow.fillna(0.0)
    out["total_requests"] = out.primary_requests + out.alternate_surface_requests + out.migration_inflow
    # Do not expose hidden responder labels or ground truth in the analytical outcome table.
    analytical = out.drop(columns=[c for c in ["raw_requests", "raw_primary_requests", "raw_alt_requests", "accepted"] if c in out.columns])
    return analytical, pd.DataFrame(manifest_rows)


def _cluster_changes(panel: pd.DataFrame, outcome: str, upto: pd.Timestamp | None = None, subset: pd.Series | None = None) -> pd.DataFrame:
    d = panel.copy()
    if upto is not None:
        d = d[d.event_date <= upto]
    if subset is not None:
        d = d[subset.reindex(d.index, fill_value=False)]
    pre = d[d.post.eq(0)].groupby(["cluster_id", "arm"])[outcome].mean().rename("pre")
    post = d[d.post.eq(1)].groupby(["cluster_id", "arm"])[outcome].mean().rename("post")
    ch = pd.concat([pre, post], axis=1).dropna().reset_index()
    ch["change"] = ch.post - ch.pre
    return ch


def _effect(panel: pd.DataFrame, outcome: str, treated_arm: str = "canary", control_arm: str = "control", upto: pd.Timestamp | None = None, account_filter: set[str] | None = None) -> dict:
    d = panel if account_filter is None else panel[panel.account_id.isin(account_filter)]
    ch = _cluster_changes(d, outcome, upto=upto)
    t = ch[ch.arm.eq(treated_arm)].change.to_numpy(dtype=float); c = ch[ch.arm.eq(control_arm)].change.to_numpy(dtype=float)
    est = float(t.mean() - c.mean()) if len(t) and len(c) else np.nan
    se = float(math.sqrt((np.var(t, ddof=1) / len(t) if len(t) > 1 else 0.0) + (np.var(c, ddof=1) / len(c) if len(c) > 1 else 0.0))) if len(t) and len(c) else np.nan
    return {"estimate": est, "se": se, "ci95_low": est - 1.96 * se if np.isfinite(se) else np.nan, "ci95_high": est + 1.96 * se if np.isfinite(se) else np.nan, "n_treated_clusters": int(len(t)), "n_control_clusters": int(len(c))}


def _pretrend(panel: pd.DataFrame, outcome: str = "total_requests") -> pd.DataFrame:
    pre = panel[panel.post.eq(0)].groupby(["event_date", "arm"])[outcome].mean().unstack()
    rows = []
    for arm in ARMS:
        y = pre[arm].dropna().to_numpy(dtype=float) if arm in pre else np.array([])
        slope = float(np.polyfit(np.arange(len(y)), y, 1)[0]) if len(y) >= 2 else np.nan
        rows.append({"arm": arm, "pretrend_slope": slope})
    out = pd.DataFrame(rows)
    control = float(out.loc[out.arm.eq("control"), "pretrend_slope"].iloc[0]) if out.arm.eq("control").any() else np.nan
    out["slope_gap_vs_control"] = out.pretrend_slope - control
    out["diagnostic_status"] = np.where(out.slope_gap_vs_control.abs() <= 0.15, "within_diagnostic_tolerance", "review_parallel_trend_risk")
    return out


def _heterogeneous_effects(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for slice_col in ["plan", "managed_infrastructure", "region"]:
        for value in sorted(panel[slice_col].dropna().unique(), key=str):
            ids = set(panel.loc[panel[slice_col].eq(value), "account_id"].unique())
            e = _effect(panel, "total_requests", account_filter=ids)
            reportable = int(e["n_treated_clusters"] >= 3 and e["n_control_clusters"] >= 3)
            rows.append({"slice_type": slice_col, "slice_value": value, **e, "reportable": reportable, "interpretation": "diagnostic heterogeneity; do not promote slice-specific policy without multiplicity/evidence review"})
    return pd.DataFrame(rows)


def _sequential_monitor(panel: pd.DataFrame, assignment: pd.DataFrame) -> pd.DataFrame:
    max_date = panel.event_date.max(); checkpoints = []
    d = ROLLOUT + pd.Timedelta(days=6)
    while d <= max_date:
        checkpoints.append(d); d += pd.Timedelta(days=7)
    if not checkpoints or checkpoints[-1] < max_date:
        checkpoints.append(max_date)
    rows = []
    for look, cp in enumerate(checkpoints, start=1):
        primary = _effect(panel, "primary_requests", upto=cp)
        total = _effect(panel, "total_requests", upto=cp)
        alt = _effect(panel, "alternate_surface_requests", upto=cp)
        acceptance = _effect(panel, "acceptance_rate", upto=cp)
        neg = _effect(panel, "prompt_chars_mean", upto=cp)
        displacement_ratio = float(max(0.0, alt["estimate"]) / max(1e-9, -primary["estimate"])) if np.isfinite(primary["estimate"]) and primary["estimate"] < 0 and np.isfinite(alt["estimate"]) else np.nan
        # Conservative 99% descriptive monitoring boundary; not a formal group-sequential design.
        primary_low = primary["estimate"] - 2.58 * primary["se"] if np.isfinite(primary["se"]) else np.nan
        primary_high = primary["estimate"] + 2.58 * primary["se"] if np.isfinite(primary["se"]) else np.nan
        if np.isfinite(acceptance["estimate"]) and acceptance["estimate"] < -0.03:
            action = "rollback_to_shadow_user_impact_guardrail"
        elif np.isfinite(displacement_ratio) and displacement_ratio > 0.60:
            action = "pause_and_review_displacement"
        elif np.isfinite(primary_high) and primary_high < 0:
            action = "continue_canary_collect_evidence"
        else:
            action = "hold_canary_collect_more_evidence"
        rows.append({
            "look": look,
            "checkpoint": cp.date().isoformat(),
            "primary_itt": primary["estimate"],
            "primary_monitor_99_low": primary_low,
            "primary_monitor_99_high": primary_high,
            "total_requests_itt": total["estimate"],
            "alternate_surface_itt": alt["estimate"],
            "acceptance_rate_itt": acceptance["estimate"],
            "negative_control_prompt_chars_itt": neg["estimate"],
            "displacement_ratio": displacement_ratio,
            "recommended_action": action,
            "sequential_boundary": "conservative 99% descriptive monitoring; human review required; not formal alpha-spending proof",
        })
    return pd.DataFrame(rows)


def _review_guardrails(data_dir: Path, assignment: pd.DataFrame) -> pd.DataFrame:
    reviews = pd.read_csv(data_dir / "reviews.csv")
    reviews["review_date"] = pd.to_datetime(reviews.review_date, utc=True, format="mixed")
    r = reviews[reviews.review_date >= ROLLOUT].merge(assignment[["account_id", "arm"]], on="account_id", how="inner")
    rows = []
    for arm in ARMS:
        g = r[r.arm.eq(arm)]
        enforced = g[g.enforcement_action.ne("none")]
        appeals = enforced[enforced.appeal_filed.eq(1)]
        rows.append({
            "arm": arm,
            "matured_reviews": int(len(g)),
            "cleared_rate": float(g.final_outcome.eq("cleared").mean()) if len(g) else np.nan,
            "enforcement_rate": float(g.enforcement_action.ne("none").mean()) if len(g) else np.nan,
            "appeal_rate_among_enforced": float(enforced.appeal_filed.mean()) if len(enforced) else np.nan,
            "overturn_rate_among_appeals": float(appeals.appeal_outcome.eq("overturned").mean()) if len(appeals) else np.nan,
            "evidence_status": "reportable" if len(g) >= 3 else "limited_matured_review_evidence",
        })
    return pd.DataFrame(rows)


def evaluate_policy_experiment(data_dir: str | Path, out_dir: str | Path, seed: int = 17) -> dict:
    data_dir = Path(data_dir); out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    accounts = pd.read_csv(data_dir / "accounts.csv")
    telemetry = pd.read_csv(data_dir / "telemetry.csv")
    telemetry["timestamp"] = pd.to_datetime(telemetry.timestamp, utc=True, format="mixed")
    assignment, ip_edges = _build_preperiod_assignment(accounts, telemetry, seed)
    panel = _daily_panel(telemetry, assignment)
    panel, manifest = _inject_hidden_policy_effect(panel, accounts, ip_edges, seed)
    manifest.to_csv(data_dir / "hidden_policy_experiment_manifest.csv", index=False)

    # IP context is a weak neighborhood for interference analysis only; it never proves common control.
    arm_map = assignment.set_index("account_id").arm.to_dict()
    if len(ip_edges):
        ip_edges["arm_a"] = ip_edges.account_a.map(arm_map); ip_edges["arm_b"] = ip_edges.account_b.map(arm_map)
        ip_edges["cross_arm"] = ip_edges.arm_a.ne(ip_edges.arm_b).astype(int)
    cross_arm_ip = int(ip_edges.cross_arm.sum()) if len(ip_edges) else 0
    total_ip = int(len(ip_edges))
    strong_cluster_cross_arm = 0  # strong org/token/payment links are unioned before cluster randomization by construction.
    interference = pd.DataFrame([
        {"network":"strong_org_token_payment_cluster","pairs_or_links":int(assignment.cluster_id.nunique()),"cross_arm_links":strong_cluster_cross_arm,"cross_arm_share":0.0,"identity_boundary":"cluster randomization unit; still not an enforcement identity verdict"},
        {"network":"ip_context_neighbors","pairs_or_links":total_ip,"cross_arm_links":cross_arm_ip,"cross_arm_share":cross_arm_ip/max(1,total_ip),"identity_boundary":"IP context only; never proves common control; used only for spillover sensitivity"},
    ])

    primary = _effect(panel, "primary_requests")
    total = _effect(panel, "total_requests")
    alt = _effect(panel, "alternate_surface_requests")
    acceptance = _effect(panel, "acceptance_rate")
    negative = _effect(panel, "prompt_chars_mean")
    shadow_placebo = _effect(panel, "total_requests", treated_arm="shadow")
    exposure_rate = float(assignment.loc[assignment.arm.eq("canary"), "exposed"].mean()) if assignment.arm.eq("canary").any() else np.nan
    att = primary["estimate"] / exposure_rate if np.isfinite(exposure_rate) and exposure_rate > 0 else np.nan
    att_low = primary["ci95_low"] / exposure_rate if np.isfinite(att) else np.nan
    att_high = primary["ci95_high"] / exposure_rate if np.isfinite(att) else np.nan
    displacement_ratio = float(max(0.0, alt["estimate"]) / max(1e-9, -primary["estimate"])) if np.isfinite(primary["estimate"]) and primary["estimate"] < 0 and np.isfinite(alt["estimate"]) else np.nan

    effect_rows = [
        {"estimand":"ITT_canary_vs_control","outcome":"primary_requests","estimate":primary["estimate"],"ci95_low":primary["ci95_low"],"ci95_high":primary["ci95_high"],"n_treated_clusters":primary["n_treated_clusters"],"n_control_clusters":primary["n_control_clusters"],"interpretation":"cluster-randomized synthetic ITT; assignment and eligibility use pre-rollout data only"},
        {"estimand":"Wald_ATT_style","outcome":"primary_requests","estimate":att,"ci95_low":att_low,"ci95_high":att_high,"n_treated_clusters":primary["n_treated_clusters"],"n_control_clusters":primary["n_control_clusters"],"interpretation":"ITT divided by canary exposure rate; requires exclusion/monotonicity-style assumptions and is diagnostic only"},
        {"estimand":"ITT_canary_vs_control","outcome":"total_requests","estimate":total["estimate"],"ci95_low":total["ci95_low"],"ci95_high":total["ci95_high"],"n_treated_clusters":total["n_treated_clusters"],"n_control_clusters":total["n_control_clusters"],"interpretation":"net behavior after within-account displacement and synthetic migration inflow"},
        {"estimand":"ITT_canary_vs_control","outcome":"alternate_surface_requests","estimate":alt["estimate"],"ci95_low":alt["ci95_low"],"ci95_high":alt["ci95_high"],"n_treated_clusters":alt["n_treated_clusters"],"n_control_clusters":alt["n_control_clusters"],"interpretation":"positive movement can indicate behavior displacement rather than true harm reduction"},
        {"estimand":"ITT_canary_vs_control","outcome":"acceptance_rate_guardrail","estimate":acceptance["estimate"],"ci95_low":acceptance["ci95_low"],"ci95_high":acceptance["ci95_high"],"n_treated_clusters":acceptance["n_treated_clusters"],"n_control_clusters":acceptance["n_control_clusters"],"interpretation":"user-experience guardrail; material negative movement blocks widening"},
        {"estimand":"negative_control_ITT","outcome":"prompt_chars_mean","estimate":negative["estimate"],"ci95_low":negative["ci95_low"],"ci95_high":negative["ci95_high"],"n_treated_clusters":negative["n_treated_clusters"],"n_control_clusters":negative["n_control_clusters"],"interpretation":"negative-control diagnostic; a material effect suggests imbalance or model misspecification"},
        {"estimand":"shadow_placebo_vs_control","outcome":"total_requests","estimate":shadow_placebo["estimate"],"ci95_low":shadow_placebo["ci95_low"],"ci95_high":shadow_placebo["ci95_high"],"n_treated_clusters":shadow_placebo["n_treated_clusters"],"n_control_clusters":shadow_placebo["n_control_clusters"],"interpretation":"shadow has no user-facing policy; material effect is a randomization/pretrend warning"},
    ]
    effects = pd.DataFrame(effect_rows)
    pretrend = _pretrend(panel)
    hte = _heterogeneous_effects(panel)
    sequential = _sequential_monitor(panel, assignment)
    reviews = _review_guardrails(data_dir, assignment)

    final_seq = sequential.iloc[-1] if len(sequential) else None
    canary_review = reviews[reviews.arm.eq("canary")].iloc[0] if reviews.arm.eq("canary").any() else None
    guardrail_reasons = []
    if np.isfinite(acceptance["estimate"]) and acceptance["estimate"] < -0.03:
        guardrail_reasons.append("acceptance_rate_harm")
    if np.isfinite(displacement_ratio) and displacement_ratio > 0.60:
        guardrail_reasons.append("high_behavior_displacement")
    if pretrend.loc[pretrend.arm.eq("canary"), "diagnostic_status"].eq("review_parallel_trend_risk").any():
        guardrail_reasons.append("pretrend_risk")
    if canary_review is not None and int(canary_review.matured_reviews) >= 3 and float(canary_review.cleared_rate) > 0.35:
        guardrail_reasons.append("high_matured_clearance_rate")
    if final_seq is not None and str(final_seq.recommended_action).startswith("rollback"):
        guardrail_reasons.append("sequential_user_impact_stop")
    if guardrail_reasons:
        recommended = "rollback_or_pause_to_shadow_for_review"
    elif np.isfinite(primary["ci95_high"]) and primary["ci95_high"] < 0:
        recommended = "continue_limited_canary_collect_matured_evidence"
    else:
        recommended = "hold_current_canary_collect_more_evidence"

    stopping = {
        "recommended_state": recommended,
        "guardrail_reasons": guardrail_reasons,
        "primary_itt": primary["estimate"],
        "primary_itt_ci95": [primary["ci95_low"], primary["ci95_high"]],
        "exposure_rate_canary": exposure_rate,
        "wald_att_style": att,
        "displacement_ratio": displacement_ratio,
        "automatic_policy_expansion_allowed": False,
        "decision_boundary": "human policy-owner review required; sequential diagnostics never auto-expand or auto-enforce",
    }

    # Benchmark-only truth is consulted only after assignment and analytical estimates are fixed.
    responder_exposed = manifest[(manifest.true_responder.eq(1)) & (manifest.injected_primary_fraction_reduction > 0)]
    benchmark = {
        "hidden_manifest_present": True,
        "manifest_used_by_assignment": False,
        "manifest_used_by_effect_estimation": False,
        "eligible_accounts": int(len(assignment)),
        "randomization_clusters": int(assignment.cluster_id.nunique()),
        "canary_exposure_rate": exposure_rate,
        "hidden_exposed_responders": int(len(responder_exposed)),
        "hidden_migration_sources": int(manifest.injected_neighbor_migration_fraction.gt(0).sum()),
        "estimated_primary_itt": primary["estimate"],
        "estimated_total_itt": total["estimate"],
        "benchmark_boundary": "hidden responder/migration manifest is benchmark-only and never used by assignment, estimation, HTE, or stopping-rule calculations",
    }

    assignment.to_csv(out_dir / "policy_experiment_assignment.csv", index=False)
    panel.to_csv(out_dir / "policy_experiment_daily_outcomes.csv", index=False)
    effects.to_csv(out_dir / "policy_experiment_effect_summary.csv", index=False)
    pretrend.to_csv(out_dir / "policy_experiment_pretrend.csv", index=False)
    hte.to_csv(out_dir / "policy_experiment_heterogeneous_effects.csv", index=False)
    sequential.to_csv(out_dir / "policy_experiment_sequential_monitor.csv", index=False)
    interference.to_csv(out_dir / "policy_experiment_interference_audit.csv", index=False)
    reviews.to_csv(out_dir / "policy_experiment_review_guardrails.csv", index=False)
    (out_dir / "policy_experiment_stopping_decision.json").write_text(json.dumps(stopping, indent=2))
    (out_dir / "policy_experiment_benchmark.json").write_text(json.dumps(benchmark, indent=2))
    return {
        "assignment": assignment,
        "effects": effects,
        "pretrend": pretrend,
        "hte": hte,
        "sequential": sequential,
        "interference": interference,
        "reviews": reviews,
        "stopping": stopping,
        "benchmark": benchmark,
    }
