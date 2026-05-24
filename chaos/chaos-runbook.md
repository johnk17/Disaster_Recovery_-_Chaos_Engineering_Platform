# Game Day Runbook

## 1. Pre-Game Checklist
- [ ] Verify Velero backup completed within the last 4 hours
- [ ] Confirm Grafana dashboards are live and baseline metrics captured
- [ ] Notify on-call team, freeze production deployments for the window
- [ ] Set Chaos Mesh namespace selector to staging only

## 2. Experiment Matrix

| Experiment Name | Tool | Duration | Blast Radius | Rollback Command |
| --- | --- | --- | --- | --- |
| Pod Kill | Chaos Mesh | 5 mins | 1 pod per 60s | `kubectl delete podchaos pod-kill -n production` |
| Network Delay | Chaos Mesh | 3 mins | Egress from app pods | `kubectl delete networkchaos network-delay -n production` |
| CPU Stress | Chaos Mesh | 2 mins | 2 app pods | `kubectl delete stresschaos cpu-stress -n production` |
| DNS Failure | Chaos Mesh | 1 min | DNS resolution from app pods | `kubectl delete dnschaos dns-failure -n production` |

## 3. Hypothesis & SLO Targets
- **Availability**: >= 99.9% during experiment
- **Error rate**: < 0.1%
- **Recovery time objective (RTO)**: < 5 minutes
- **Recovery point objective (RPO)**: < 15 minutes

## 4. Observation Protocol
- **Prometheus queries to watch**:
  - `rate(http_server_requests_seconds_count{status=~"5.."}[1m])`
  - `jvm_memory_used_bytes{area="heap"}`
- **Grafana panels to screenshot**:
  - Request rate, P50/P95/P99 latency
  - Active chaos experiments
- **Actuator checks**:
  - Access `/actuator/health` to verify components (liveness, readiness).

## 5. Post-Game Analysis Template
- **What broke**:
- **What held**:
- **What surprised us**:
- **Metrics comparison (before/during/after)**:
- **Action items with owners and deadlines**:

## Execution Commands
- **Apply**: `kubectl apply -f <experiment.yaml>`
- **Monitor**: Check Chaos Mesh Dashboard (`kubectl port-forward svc/chaos-dashboard 2333:2333 -n chaos-testing`)
- **Delete**: `kubectl delete -f <experiment.yaml>`
