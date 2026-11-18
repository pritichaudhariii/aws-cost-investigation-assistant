---
title: Over-provisioned RDS instances
category: rds_overprovisioned
service: AmazonRDS
usage_type_pattern: InstanceUsage
allowed_roles: engineer,finance,admin
---

# Over-provisioned RDS instances

## Symptoms
A new `InstanceUsage:db.*` line item for a large instance class with low CPU and connections.

## Fix
- Right-size using Performance Insights and Compute Optimizer recommendations.
- Use Aurora Serverless v2 or stop non-production databases outside working hours.
- Consider Graviton (r6g/r7g) classes and Reserved Instances for steady workloads.
