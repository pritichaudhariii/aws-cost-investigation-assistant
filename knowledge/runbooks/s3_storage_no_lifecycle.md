---
title: S3 storage growth without lifecycle rules
category: s3_storage_no_lifecycle
service: AmazonS3
usage_type_pattern: TimedStorage
allowed_roles: engineer,finance,admin
---

# S3 storage growth without lifecycle rules

## Symptoms
`TimedStorage-ByteHrs` for one bucket grows continuously. Usually a log, raw-data or backup bucket.

## Fix
- Add lifecycle rules: transition to S3 Glacier Instant Retrieval or Deep Archive after N days, expire after the retention period.
- Expire non-current versions and incomplete multipart uploads.
- Consider S3 Intelligent-Tiering for unknown access patterns.
