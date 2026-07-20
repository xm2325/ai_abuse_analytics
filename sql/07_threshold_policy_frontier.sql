-- Threshold policy frontier for human-review queue planning.
-- Assumes account_risk_scores contains matured evaluation labels for the review window.
WITH candidate_thresholds AS (
  SELECT 0.50 AS threshold UNION ALL SELECT 0.60 UNION ALL SELECT 0.70 UNION ALL SELECT 0.80 UNION ALL SELECT 0.90
), scored AS (
  SELECT t.threshold, r.account_id, r.label, r.risk_score, r.managed_infrastructure,
         CASE WHEN r.risk_score >= t.threshold THEN 1 ELSE 0 END AS flagged
  FROM candidate_thresholds t CROSS JOIN account_risk_scores r
  WHERE r.split='holdout'
)
SELECT threshold,
       AVG(flagged*1.0) AS review_workload_share,
       SUM(CASE WHEN label=1 AND flagged=1 THEN 1 ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN flagged=1 THEN 1 ELSE 0 END),0) AS precision,
       SUM(CASE WHEN label=1 AND flagged=1 THEN 1 ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN label=1 THEN 1 ELSE 0 END),0) AS recall,
       SUM(CASE WHEN label=0 AND flagged=1 THEN 1 ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN label=0 THEN 1 ELSE 0 END),0) AS false_positive_rate
FROM scored GROUP BY threshold ORDER BY threshold;
