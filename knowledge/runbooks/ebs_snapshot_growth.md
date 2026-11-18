---
title: EBS snapshot accumulation
category: ebs_snapshot_growth
service: AmazonEC2
usage_type_pattern: EBS:SnapshotUsage
allowed_roles: engineer,finance,admin
---

# EBS snapshot accumulation

## Symptoms
`EBS:SnapshotUsage` grows steadily day over day rather than as a step change.

## Common causes
- Backup scripts creating snapshots with no deletion.
- AMIs deregistered while their snapshots remain.

## Fix
- Move to **Amazon Data Lifecycle Manager** or AWS Backup with a retention rule (for example 7 daily, 4 weekly).
- Delete orphaned snapshots whose source volume or AMI no longer exists.
- Use the EBS Snapshots Archive tier for long-term retention.
