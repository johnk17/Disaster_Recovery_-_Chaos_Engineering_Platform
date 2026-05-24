# Multi-AZ Failure Simulation & Recovery Procedure

**Scenario**: Simulate the loss of `us-east-1a` to test EKS topology spread constraints and application resilience.

## Step 1 — Simulate AZ Loss
Cordon and drain all nodes in the affected AZ:
```bash
kubectl cordon -l topology.kubernetes.io/zone=us-east-1a
kubectl drain -l topology.kubernetes.io/zone=us-east-1a --ignore-daemonsets --delete-emptydir-data
```

## Step 2 — Observe Rescheduling
Verify that pods are rescheduled to `us-east-1b` and `us-east-1c` within 2 minutes:
```bash
kubectl get pods -n production -o wide
```
Check Prometheus metric: Ensure `kube_pod_status_phase` is `Running` for all replicas.

## Step 3 — Traffic Validation
Run 1000 requests to assert 0% errors during the shift:
```bash
ab -n 1000 -c 10 http://my-service.production.svc.cluster.local:8080/actuator/health
# Or via curl loop checking HTTP status
```

## Step 4 — AZ Recovery
Uncordon the nodes to simulate the AZ coming back online:
```bash
kubectl uncordon -l topology.kubernetes.io/zone=us-east-1a
```
Verify EKS re-balances pods via topology spread constraints over time.

## Step 5 — Document Findings
Record the following:
- Actual RTO:
- Failed Pods (if any):
- Grafana Alerts Fired:
