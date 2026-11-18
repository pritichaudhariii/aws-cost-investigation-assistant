# Evaluation results

| Metric | Value |
|---|---|
| role | engineer |
| retrieval_mode | driver |
| scenarios | 30 |
| root_cause_accuracy | 1.0 |
| driver_accuracy | 1.0 |
| retrieval_hit@1 | 1.0 |
| retrieval_hit@3 | 1.0 |
| mrr | 1.0 |
| latency_p50_ms | 15.4 |
| latency_p95_ms | 19.7 |
| cost_per_query_usd | 0.0 |
| isolation_violations | 0 |
| cross_team_requests_blocked | 30 |
| pii_leaks | 0 |

| Scenario | Labelled cause | Predicted | Correct | Top driver correct | Gold runbook rank | Latency (ms) |
|---|---|---|---|---|---|---|
| S01 | nat_gateway_data_processing | nat_gateway_data_processing | yes | yes | 1 | 21.2 |
| S02 | idle_ec2_instances | idle_ec2_instances | yes | yes | 1 | 16.3 |
| S03 | ebs_snapshot_growth | ebs_snapshot_growth | yes | yes | 1 | 15.3 |
| S04 | s3_request_spike | s3_request_spike | yes | yes | 1 | 14.8 |
| S05 | s3_storage_no_lifecycle | s3_storage_no_lifecycle | yes | yes | 1 | 16.8 |
| S06 | cloudwatch_logs_ingestion | cloudwatch_logs_ingestion | yes | yes | 1 | 14.3 |
| S07 | lambda_recursive_loop | lambda_recursive_loop | yes | yes | 1 | 14.9 |
| S08 | rds_overprovisioned | rds_overprovisioned | yes | yes | 1 | 15.6 |
| S09 | dynamodb_on_demand_spike | dynamodb_on_demand_spike | yes | yes | 1 | 17.0 |
| S10 | cross_region_transfer | cross_region_transfer | yes | yes | 1 | 14.8 |
| S11 | nat_gateway_data_processing | nat_gateway_data_processing | yes | yes | 1 | 14.1 |
| S12 | idle_ec2_instances | idle_ec2_instances | yes | yes | 1 | 15.0 |
| S13 | ebs_snapshot_growth | ebs_snapshot_growth | yes | yes | 1 | 14.9 |
| S14 | s3_request_spike | s3_request_spike | yes | yes | 1 | 15.0 |
| S15 | s3_storage_no_lifecycle | s3_storage_no_lifecycle | yes | yes | 1 | 15.1 |
| S16 | cloudwatch_logs_ingestion | cloudwatch_logs_ingestion | yes | yes | 1 | 13.6 |
| S17 | lambda_recursive_loop | lambda_recursive_loop | yes | yes | 1 | 14.0 |
| S18 | rds_overprovisioned | rds_overprovisioned | yes | yes | 1 | 14.5 |
| S19 | dynamodb_on_demand_spike | dynamodb_on_demand_spike | yes | yes | 1 | 14.1 |
| S20 | cross_region_transfer | cross_region_transfer | yes | yes | 1 | 15.1 |
| S21 | nat_gateway_data_processing | nat_gateway_data_processing | yes | yes | 1 | 17.1 |
| S22 | idle_ec2_instances | idle_ec2_instances | yes | yes | 1 | 19.8 |
| S23 | ebs_snapshot_growth | ebs_snapshot_growth | yes | yes | 1 | 19.5 |
| S24 | s3_request_spike | s3_request_spike | yes | yes | 1 | 16.3 |
| S25 | s3_storage_no_lifecycle | s3_storage_no_lifecycle | yes | yes | 1 | 17.5 |
| S26 | cloudwatch_logs_ingestion | cloudwatch_logs_ingestion | yes | yes | 1 | 16.6 |
| S27 | lambda_recursive_loop | lambda_recursive_loop | yes | yes | 1 | 17.7 |
| S28 | rds_overprovisioned | rds_overprovisioned | yes | yes | 1 | 17.8 |
| S29 | dynamodb_on_demand_spike | dynamodb_on_demand_spike | yes | yes | 1 | 17.8 |
| S30 | cross_region_transfer | cross_region_transfer | yes | yes | 1 | 19.4 |
