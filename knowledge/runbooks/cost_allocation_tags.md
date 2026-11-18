---
title: Cost allocation and tagging policy
category: general
service: *
usage_type_pattern: 
allowed_roles: engineer,finance,admin
---

# Cost allocation and tagging policy

## Policy
Every resource must carry `team`, `service` and `env` tags. Untagged spend is reported weekly to engineering managers.

## Investigating any anomaly
1. Identify the account, service and usage type with the largest change versus the trailing baseline.
2. Drill into resource IDs first seen in the anomaly window.
3. Use CloudTrail to find who created the resource and when.
4. Open a ticket with the owning team and link this investigation.
