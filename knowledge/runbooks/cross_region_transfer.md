---
title: Inter-region data transfer
category: cross_region_transfer
service: AWSDataTransfer
usage_type_pattern: AWS-Out-Bytes
allowed_roles: engineer,finance,admin
---

# Inter-region data transfer

## Symptoms
Usage types such as `USE1-USW2-AWS-Out-Bytes` (inter-region transfer) increase.

## Common causes
- S3 Cross-Region Replication of a high-churn bucket.
- Services in one region reading from a database or bucket in another.

## Fix
- Replicate only the prefixes that need DR; filter by tag.
- Keep compute and data in the same region; use read replicas in the consuming region.
