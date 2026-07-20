-- v0.9 policy experimentation / causal evaluation examples
-- Defensive analyst workflow only. These queries do not define production enforcement policy.

-- 1) Assignment integrity: one randomization cluster must map to exactly one arm.
SELECT
  cluster_id,
  COUNT(DISTINCT arm) AS arm_count,
  COUNT(DISTINCT account_id) AS accounts
FROM policy_experiment_assignment
GROUP BY cluster_id
HAVING COUNT(DISTINCT arm) <> 1;

-- Expected result: zero rows.


-- 2) Arm balance using pre-rollout-only covariates.
SELECT
  arm,
  COUNT(*) AS accounts,
  COUNT(DISTINCT cluster_id) AS clusters,
  AVG(pre_requests_per_active_day) AS avg_pre_requests_per_active_day,
  AVG(pre_policy_signal_rate) AS avg_pre_policy_signal_rate,
  AVG(managed_infrastructure) AS managed_infrastructure_share
FROM policy_experiment_assignment
GROUP BY arm
ORDER BY arm;


-- 3) Cluster-level pre/post change for the primary outcome.
WITH cluster_period AS (
  SELECT
    cluster_id,
    arm,
    post,
    AVG(primary_requests) AS mean_primary_requests
  FROM policy_experiment_daily_outcomes
  GROUP BY 1,2,3
), changes AS (
  SELECT
    cluster_id,
    arm,
    MAX(CASE WHEN post=1 THEN mean_primary_requests END)
      - MAX(CASE WHEN post=0 THEN mean_primary_requests END) AS change_primary
  FROM cluster_period
  GROUP BY 1,2
)
SELECT
  arm,
  COUNT(*) AS clusters,
  AVG(change_primary) AS avg_change_primary
FROM changes
GROUP BY arm
ORDER BY arm;

-- The causal comparison is the difference in mean cluster changes between assigned canary and control.
-- Do not switch to account-level naive standard errors when assignment occurred at cluster level.


-- 4) Displacement check: targeted surface falls, but alternate surface rises.
WITH arm_period AS (
  SELECT
    arm,
    post,
    AVG(primary_requests) AS primary_mean,
    AVG(alternate_surface_requests) AS alternate_mean,
    AVG(total_requests) AS total_mean
  FROM policy_experiment_daily_outcomes
  GROUP BY 1,2
), changes AS (
  SELECT
    arm,
    MAX(CASE WHEN post=1 THEN primary_mean END)-MAX(CASE WHEN post=0 THEN primary_mean END) AS primary_change,
    MAX(CASE WHEN post=1 THEN alternate_mean END)-MAX(CASE WHEN post=0 THEN alternate_mean END) AS alternate_change,
    MAX(CASE WHEN post=1 THEN total_mean END)-MAX(CASE WHEN post=0 THEN total_mean END) AS total_change
  FROM arm_period
  GROUP BY arm
)
SELECT *
FROM changes
ORDER BY arm;

-- A large negative primary_change with little/no negative total_change is a displacement warning,
-- not evidence of equivalent harm reduction.


-- 5) Shadow placebo / negative-control review.
SELECT
  estimand,
  outcome,
  estimate,
  ci95_low,
  ci95_high,
  interpretation
FROM policy_experiment_effect_summary
WHERE estimand IN ('shadow_placebo_vs_control','negative_control_ITT');

-- Material effects here should trigger assignment/pre-trend/model review before causal claims.


-- 6) Sequential canary decision log.
SELECT
  look,
  checkpoint,
  primary_itt,
  primary_monitor_99_low,
  primary_monitor_99_high,
  total_requests_itt,
  alternate_surface_itt,
  acceptance_rate_itt,
  displacement_ratio,
  recommended_action
FROM policy_experiment_sequential_monitor
ORDER BY look;

-- The recommended_action is decision support only; no SQL row auto-expands or auto-rolls back policy.


-- 7) Heterogeneous treatment-effect diagnostics with evidence-volume filter.
SELECT
  slice_type,
  slice_value,
  estimate,
  ci95_low,
  ci95_high,
  n_treated_clusters,
  n_control_clusters,
  reportable
FROM policy_experiment_heterogeneous_effects
WHERE reportable = 1
ORDER BY ABS(estimate) DESC;

-- Exploratory only. Review multiplicity, power, stability, user impact, and policy/legal implications
-- before considering slice-specific treatment.


-- 8) Interference audit.
SELECT
  network,
  pairs_or_links,
  cross_arm_links,
  cross_arm_share,
  identity_boundary
FROM policy_experiment_interference_audit;

-- Strong org/token/payment links should be contained within randomization clusters.
-- IP-context overlap is weak context for spillover sensitivity only and never proves common control.


-- 9) Matured review / appeal guardrails by arm.
SELECT
  arm,
  matured_reviews,
  cleared_rate,
  enforcement_rate,
  appeal_rate_among_enforced,
  overturn_rate_among_appeals,
  evidence_status
FROM policy_experiment_review_guardrails
ORDER BY arm;

-- Do not interpret unstable percentages from tiny matured-review samples as policy evidence.
