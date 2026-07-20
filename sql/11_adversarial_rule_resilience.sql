-- v0.8 adversarial adaptation / detection resilience workflow
--
-- This SQL is defensive analytics support. It does not expose or reproduce any real
-- GitHub/Copilot control thresholds. Replace benchmark columns/limits with approved
-- internal semantic views only in a governed environment.

-- 1) Monitor concentration near a review boundary without publishing an exact threshold.
-- The purpose is to detect distributional bunching / gaming pressure over time.
WITH daily_risk AS (
    SELECT
        DATE(event_date) AS event_date,
        COUNT(*) AS accounts,
        AVG(risk_score) AS mean_risk,
        SUM(CASE WHEN risk_band = 'near_review_boundary' THEN 1 ELSE 0 END) AS near_boundary_accounts
    FROM account_review_daily
    GROUP BY 1
)
SELECT
    event_date,
    accounts,
    mean_risk,
    near_boundary_accounts,
    1.0 * near_boundary_accounts / NULLIF(accounts, 0) AS near_boundary_share
FROM daily_risk
ORDER BY event_date;

-- 2) Rule-overlap monitoring: when behavior adapts, a previously corroborated rule may
-- become increasingly isolated. That is a resilience warning, not proof of evasion.
SELECT
    event_date,
    rule_id,
    COUNT(*) AS triggered_accounts,
    AVG(independent_signal_family_count) AS avg_independent_signal_families,
    AVG(CASE WHEN independent_signal_family_count >= 2 THEN 1.0 ELSE 0.0 END) AS corroborated_share,
    AVG(review_confirmed_abuse) AS matured_confirmation_rate
FROM rule_trigger_daily
WHERE label_matured = 1
GROUP BY event_date, rule_id
ORDER BY event_date, rule_id;

-- 3) Canary/rollback watch: compare current operational metrics with a frozen baseline.
-- Exact guardrails should live in governed configuration, not public SQL.
SELECT
    rule_id,
    rule_version,
    current_stage,
    current_review_workload_share,
    baseline_review_workload_share,
    current_false_positive_rate,
    baseline_false_positive_rate,
    current_appeal_overturn_rate,
    baseline_appeal_overturn_rate,
    CASE
        WHEN data_contract_status <> 'pass' THEN 'rollback_or_pause_data_incident'
        WHEN current_review_workload_share > approved_workload_guardrail THEN 'rollback_or_reduce_canary'
        WHEN current_false_positive_rate > approved_fpr_guardrail THEN 'rollback_or_reduce_canary'
        WHEN current_appeal_overturn_rate > approved_overturn_guardrail THEN 'rollback_or_reduce_canary'
        ELSE 'continue_canary_with_monitoring'
    END AS recommended_stage_action
FROM rule_canary_health;

-- 4) Signal-diversity audit. A rule family that depends on one correlated source is more
-- brittle than one corroborated by independent sources.
SELECT
    rule_id,
    rule_version,
    COUNT(DISTINCT signal_family) AS independent_signal_families,
    GROUP_CONCAT(DISTINCT signal_family) AS signal_family_list
FROM rule_signal_dependencies
GROUP BY rule_id, rule_version;
