---
title: Idle or forgotten EC2 instances
category: idle_ec2_instances
service: AmazonEC2
usage_type_pattern: BoxUsage
allowed_roles: engineer,finance,admin
---

# Idle or forgotten EC2 instances

## Symptoms
New `BoxUsage` line items for instance IDs that did not exist before, running 24 hours a day, often of a large size (4xlarge+) used for load or performance tests.

## How to confirm
1. Group cost by `resource_id` and look for IDs first seen inside the anomaly window.
2. Check CPUUtilization in CloudWatch; under 5% average for 3 days usually means idle.
3. Look at the `Owner` / `Purpose` tags and the CloudTrail `RunInstances` event to find who launched them.

## Fix
- Stop or terminate the instances after confirming with the owner.
- Use an Auto Scaling group or scheduled scaling so test fleets scale to zero.
- Enforce a `ttl` tag with an EventBridge rule + Lambda that stops expired test instances.
