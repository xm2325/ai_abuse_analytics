-- Review outcomes are delayed labels. Recent cases are not fully matured truth.
SELECT policy_version, taxonomy_version, COUNT(*) AS reviews,
       AVG(CASE WHEN final_outcome='confirmed_abuse' THEN 1.0 ELSE 0.0 END) AS final_confirmation_rate,
       AVG(CASE WHEN appeal_filed=1 THEN 1.0 ELSE 0.0 END) AS appeal_rate,
       AVG(CASE WHEN appeal_outcome='overturned' THEN 1.0 ELSE 0.0 END) AS overturn_rate
FROM reviews GROUP BY 1,2;

SELECT enforcement_action, COUNT(*) AS reviews,
       AVG(decision_latency_hours) AS mean_decision_latency_hours
FROM reviews GROUP BY 1 ORDER BY reviews DESC;
