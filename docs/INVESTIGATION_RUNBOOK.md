# Investigation runbook

1. Start with the decision: what action could this investigation support?
2. Validate telemetry coverage and known producer incidents before interpreting a score change.
3. Read the risk score as priority, not proof.
4. Review reason codes, recent timeline, plan, managed-infrastructure context, and linked-entity evidence.
5. Test benign explanations before escalation: approved automation, enterprise NAT/VPN, managed devices, CI/agent use, security research, travel, token lifecycle, and product/entitlement changes.
6. Prefer two independent signal families: behavioral/temporal evidence plus reliable identity or entitlement evidence.
7. Treat IP sharing as supporting context only.
8. Use the approved restricted path for raw-content review when aggregate evidence is insufficient.
9. Record outcome, action, policy/taxonomy version, decision latency, appeal, and final result.
10. Return cleared and overturned cases to threshold/rule analysis.
