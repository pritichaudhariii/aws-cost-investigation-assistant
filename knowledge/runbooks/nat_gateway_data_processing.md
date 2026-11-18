---
title: NAT Gateway data processing charges
category: nat_gateway_data_processing
service: AmazonEC2
usage_type_pattern: NatGateway-Bytes
allowed_roles: engineer,finance,admin
---

# NAT Gateway data processing charges

## Symptoms
NAT Gateway charges are billed per hour **and per GB processed**. A sudden jump in `NatGateway-Bytes` usage with flat `NatGateway-Hours` means much more traffic is leaving private subnets through the gateway.

## Common causes
- Container image pulls from ECR or Docker Hub from private subnets.
- Large S3 or DynamoDB reads from private subnets without a **gateway VPC endpoint**.
- A service calling another AWS API (SQS, STS, KMS) at high volume without an interface endpoint.

## How to confirm
1. Enable VPC Flow Logs on the NAT gateway ENI and group by destination prefix list.
2. Compare destination IPs against the `com.amazonaws.<region>.s3` prefix list.
3. Check CloudWatch `BytesOutToDestination` for the gateway.

## Fix
- Add S3 and DynamoDB **gateway endpoints** (free) to the private route tables.
- Add interface endpoints for ECR (`ecr.api`, `ecr.dkr`) and other high-volume APIs.
- Cache container images or use pull-through cache rules.
