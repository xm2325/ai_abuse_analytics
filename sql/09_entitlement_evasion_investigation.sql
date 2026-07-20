-- Multi-account entitlement-pressure investigation.
-- This query produces investigation leads only. Shared billing is not proof of evasion.
WITH cycle_usage AS (
  SELECT
    e.account_id,
    e.cycle_index,
    e.cycle_start,
    e.cycle_end,
    e.billing_family_ref,
    e.billing_context,
    e.plan,
    e.managed_infrastructure,
    COUNT(t.request_id) AS requests,
    COUNT(DISTINCT DATE(t.timestamp)) AS active_days,
    e.entitlement_limit_per_active_day * MAX(1, COUNT(DISTINCT DATE(t.timestamp))) AS effective_allowance
  FROM entitlements e
  LEFT JOIN telemetry t
    ON t.account_id=e.account_id
   AND DATE(t.timestamp) BETWEEN e.cycle_start AND e.cycle_end
  GROUP BY
    e.account_id,e.cycle_index,e.cycle_start,e.cycle_end,e.billing_family_ref,
    e.billing_context,e.plan,e.managed_infrastructure,e.entitlement_limit_per_active_day
), family AS (
  SELECT
    cycle_index,
    billing_family_ref,
    COUNT(DISTINCT account_id) AS family_accounts,
    SUM(requests) AS combined_requests,
    SUM(effective_allowance) AS combined_allowance,
    SUM(CASE WHEN requests*1.0/NULLIF(effective_allowance,0)>=0.80 THEN 1 ELSE 0 END) AS near_limit_accounts,
    AVG(managed_infrastructure*1.0) AS managed_share,
    SUM(CASE WHEN billing_context='managed_shared_billing' THEN 1 ELSE 0 END) AS managed_shared_billing_accounts
  FROM cycle_usage
  GROUP BY cycle_index,billing_family_ref
)
SELECT
  *,
  combined_requests*1.0/NULLIF(combined_allowance,0) AS family_usage_ratio,
  CASE
    WHEN family_accounts>=2
     AND near_limit_accounts>=2
     AND NOT (managed_share>=0.80 OR managed_shared_billing_accounts>=2)
    THEN 'investigate_multi_account_entitlement_pressure'
    WHEN family_accounts>=2
     AND (managed_share>=0.80 OR managed_shared_billing_accounts>=2)
    THEN 'review_enterprise_shared_billing_context_before_escalation'
    ELSE 'no_multi_account_pressure'
  END AS investigation_status
FROM family
ORDER BY near_limit_accounts DESC,family_usage_ratio DESC;
