# Evaluation results

| Metric | Value |
|---|---|
| role | engineer |
| retrieval_mode | question |
| scenarios | 30 |
| root_cause_accuracy | 0.133 |
| driver_accuracy | 1.0 |
| retrieval_hit@1 | 0.133 |
| retrieval_hit@3 | 0.467 |
| mrr | 0.267 |
| latency_p50_ms | 14.4 |
| latency_p95_ms | 19.5 |
| cost_per_query_usd | 0.0 |
| isolation_violations | 0 |
| cross_team_requests_blocked | 30 |
| pii_leaks | 0 |

| Scenario | Labelled cause | Predicted | Correct | Top driver correct | Gold runbook rank | Latency (ms) |
|---|---|---|---|---|---|---|
| S01 | nat_gateway_data_processing | cross_region_transfer | no | yes | None | 26.1 |
| S02 | idle_ec2_instances | cross_region_transfer | no | yes | 3 | 17.3 |
| S03 | ebs_snapshot_growth | dynamodb_on_demand_spike | no | yes | None | 14.9 |
| S04 | s3_request_spike | dynamodb_on_demand_spike | no | yes | None | 14.5 |
| S05 | s3_storage_no_lifecycle | dynamodb_on_demand_spike | no | yes | 3 | 14.5 |
| S06 | cloudwatch_logs_ingestion | dynamodb_on_demand_spike | no | yes | None | 14.0 |
| S07 | lambda_recursive_loop | nat_gateway_data_processing | no | yes | 2 | 14.2 |
| S08 | rds_overprovisioned | dynamodb_on_demand_spike | no | yes | None | 14.2 |
| S09 | dynamodb_on_demand_spike | dynamodb_on_demand_spike | yes | yes | 1 | 13.8 |
| S10 | cross_region_transfer | cross_region_transfer | yes | yes | 1 | 14.5 |
| S11 | nat_gateway_data_processing | nat_gateway_data_processing | yes | yes | 1 | 13.2 |
| S12 | idle_ec2_instances | nat_gateway_data_processing | no | yes | None | 14.3 |
| S13 | ebs_snapshot_growth | nat_gateway_data_processing | no | yes | None | 14.0 |
| S14 | s3_request_spike | nat_gateway_data_processing | no | yes | None | 13.8 |
| S15 | s3_storage_no_lifecycle | nat_gateway_data_processing | no | yes | 2 | 14.3 |
| S16 | cloudwatch_logs_ingestion | nat_gateway_data_processing | no | yes | None | 14.8 |
| S17 | lambda_recursive_loop | nat_gateway_data_processing | no | yes | 2 | 14.1 |
| S18 | rds_overprovisioned | nat_gateway_data_processing | no | yes | None | 14.2 |
| S19 | dynamodb_on_demand_spike | nat_gateway_data_processing | no | yes | None | 13.5 |
| S20 | cross_region_transfer | nat_gateway_data_processing | no | yes | 2 | 18.0 |
| S21 | nat_gateway_data_processing | cross_region_transfer | no | yes | None | 18.1 |
| S22 | idle_ec2_instances | cross_region_transfer | no | yes | 3 | 17.1 |
| S23 | ebs_snapshot_growth | cross_region_transfer | no | yes | None | 20.5 |
| S24 | s3_request_spike | cross_region_transfer | no | yes | None | 18.3 |
| S25 | s3_storage_no_lifecycle | cross_region_transfer | no | yes | 3 | 14.4 |
| S26 | cloudwatch_logs_ingestion | cross_region_transfer | no | yes | None | 13.7 |
| S27 | lambda_recursive_loop | cross_region_transfer | no | yes | 3 | 15.3 |
| S28 | rds_overprovisioned | cross_region_transfer | no | yes | None | 14.1 |
| S29 | dynamodb_on_demand_spike | idle_ec2_instances | no | yes | 3 | 13.9 |
| S30 | cross_region_transfer | cross_region_transfer | yes | yes | 1 | 14.4 |
