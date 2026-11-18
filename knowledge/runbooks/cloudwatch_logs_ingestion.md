---
title: CloudWatch Logs ingestion cost
category: cloudwatch_logs_ingestion
service: AmazonCloudWatch
usage_type_pattern: DataProcessing-Bytes
allowed_roles: engineer,finance,admin
---

# CloudWatch Logs ingestion cost

## Symptoms
`DataProcessing-Bytes` (log ingestion) increases sharply for one log group after a deploy.

## Common causes
- DEBUG or TRACE logging enabled in production.
- Logging full request/response payloads.

## Fix
- Revert the log level; make it configurable without a redeploy.
- Use the Infrequent Access log class for logs that are rarely queried.
- Set retention on every log group (never "Never expire").
