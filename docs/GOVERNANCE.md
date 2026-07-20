# Governance and safety boundary

## Purpose

This project supports investigation prioritization, monitoring, and analytical evaluation. It does not authorize automatic enforcement.

## Default analyst data

The default layer contains hashed device/IP/payment/token fingerprints and aggregate behavioral fields. It does not expose raw prompts, completions, IP addresses, payment details, email addresses, repository contents, or raw device identifiers.

## Escalation boundary

Expanded content or identity review requires a documented purpose, minimum necessary access, appropriate privacy/legal review, access logging, retention rules, and an investigator decision record.

## False-positive safety

Shared IP or managed infrastructure is not treated as identity proof. High-intensity legitimate use, enterprise NAT/VPN, approved automation, CI/agent workflows, security research, travel, and token rotation are explicit competing explanations.

## Audit fields

Rule/taxonomy version, review outcome, enforcement action, appeal result, final outcome, and decision latency are preserved in the synthetic case contract so decisions can be reconstructed and evaluated.
