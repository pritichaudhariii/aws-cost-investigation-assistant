---
title: Lambda runaway or recursive invocations
category: lambda_recursive_loop
service: AWSLambda
usage_type_pattern: Lambda-GB-Second
allowed_roles: engineer,finance,admin
---

# Lambda runaway or recursive invocations

## Symptoms
`Lambda-GB-Second` and `Request` usage for a single function grow by orders of magnitude within hours.

## Common causes
- A function triggered by S3 that writes its output back to the **same bucket/prefix**, invoking itself recursively.
- An SQS consumer that fails and re-queues messages forever.

## Fix
- Write outputs to a different bucket or prefix and scope the trigger with a prefix/suffix filter.
- Keep Lambda recursive loop detection enabled; set reserved concurrency as a safety cap.
- Add a dead-letter queue and a maximum receive count.
