---
title: S3 request charges spike
category: s3_request_spike
service: AmazonS3
usage_type_pattern: Requests-Tier1
allowed_roles: engineer,finance,admin
---

# S3 request charges spike

## Symptoms
`Requests-Tier1` (PUT, COPY, POST, LIST) or `Requests-Tier2` (GET) charges jump while storage stays flat.

## Common causes
- A client retry loop or a misconfigured SDK backoff hammering the bucket.
- Listing a large prefix on every request instead of caching the result.
- Many tiny objects written individually instead of batched.

## How to confirm
Enable S3 server access logs or CloudTrail data events on the bucket and group by `userAgent`, `requester` and operation.

## Fix
- Fix the retry policy (exponential backoff with jitter, max attempts).
- Batch small writes; use S3 Inventory instead of repeated LIST calls.
