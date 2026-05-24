# Observability Setup Guide

## 1. Deploy Kube-Prometheus-Stack

Install the Helm chart with our custom values:
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f prometheus-stack-values.yaml
```

## 2. Apply Custom Resources

Deploy the ServiceMonitor and Custom Alerts:
```bash
kubectl apply -f service-monitor.yaml
kubectl apply -f prometheus-rules.yaml
```

## 3. Access Grafana

Port-forward Grafana to access it locally on port 3000:
```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```
**Default Credentials:**
- Username: `admin`
- Password: `prom-operator` (or what is stored in your secret)

## 4. SLO Queries (PromQL)

**Availability SLO (99.9% uptime over 30 days):**
```promql
1 - sum(rate(http_server_requests_seconds_count{status=~"5.."}[30d])) / sum(rate(http_server_requests_seconds_count[30d]))
```

**Latency SLO (95% < 200ms over 30 days):**
```promql
sum(rate(http_server_requests_seconds_bucket{le="0.2"}[30d])) / sum(rate(http_server_requests_seconds_count[30d]))
```

## 5. Import Dashboards
In Grafana, go to `Dashboards -> Import` and upload the provided JSON files:
- `grafana-dashboard-main.json`
- `grafana-dashboard-slo.json`
