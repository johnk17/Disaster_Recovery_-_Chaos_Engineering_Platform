# Cyber-Incident DR Playbook

**Scenario**: Compromised Jenkins credentials leading to a malicious deployment on EKS.

## 1. Detection
- **Prometheus alert**: Unexpected deployment event outside business hours.
- **Grafana anomaly**: Sudden spike in outbound network traffic from pods.
- **CloudTrail alert**: IAM key used from an unrecognized IP address.

## 2. Containment (First 15 Minutes)
1. **Rotate Credentials**: Rotate all Jenkins credentials and AWS IAM access keys immediately in AWS IAM Console / Vault.
2. **Scale Down**: Stop the malicious pods.
   ```bash
   kubectl scale deployment my-service --replicas=0 -n production
   ```
3. **Isolate Namespace**: Apply a NetworkPolicy to block all ingress/egress.
   ```bash
   kubectl apply -f isolate-namespace.yaml
   ```
4. **Revoke Access**: Revoke ECR push permissions from the compromised IAM role.

## 3. Eradication
1. **Restore**: Perform a Velero restore from the last known-good backup (pre-incident timestamp).
2. **Re-scan**: Re-scan the restored image with Trivy to ensure no malware was injected prior to the backup.
3. **Rotate Secrets**: Rotate all Kubernetes Secrets and ConfigMaps with sensitive values in the `production` namespace.
4. **Jenkins Pipeline**: Re-create Jenkins pipeline credentials from scratch and update the Jenkinsfile.

## 4. Recovery Validation
- Verify pod image digest matches the known-good SHA.
- Run full integration test suite via Jenkins to ensure service integrity.
- Check Spring Boot Actuator `/actuator/info` for the correct build version.

## 5. Post-Incident
- **Timeline**: Document when the breach occurred vs when containment completed.
- **Blast Radius**: What data/systems were touched?
- **Control Gaps**: How were the credentials compromised?
- **Remediation Items**: Implement stricter IAM conditions, enable MFA, improve alert response time.
