---
title: DynamoDB on-demand write spike
category: dynamodb_on_demand_spike
service: AmazonDynamoDB
usage_type_pattern: WriteRequestUnits
allowed_roles: engineer,finance,admin
---

# DynamoDB on-demand write spike

## Symptoms
`WriteRequestUnits` on an on-demand table jumps, often from a backfill or migration job.

## Fix
- Throttle the backfill; for large one-off loads use **Import from S3** (billed per GB, much cheaper than writes).
- For steady high throughput switch the table to provisioned capacity with auto scaling.
- Check for write amplification from GSIs that project all attributes.
