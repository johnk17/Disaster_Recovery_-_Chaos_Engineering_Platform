# Velero Setup and DR Runbook

## Installation
```bash
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.9.0 \
  --bucket velero-backup-20260524124012657700000006 \
  --backup-location-config region=us-east-1 \
  --snapshot-location-config region=us-east-1 \
  --use-volume-snapshots=true \
  --secret-file ./credentials-velero
```
*(Assuming IRSA is used, you can replace `--secret-file` with the proper ServiceAccount annotations for AWS IAM role ARN).*

## Scheduled Backups
Create a full namespace backup every 6 hours with retention (7 daily, 4 weekly) and include PVs:
```bash
velero schedule create full-backup \
  --schedule="0 */6 * * *" \
  --include-namespaces production \
  --snapshot-volumes=true \
  --ttl 168h # 7 days
```

## Disaster Recovery Drill
**Scenario: Accidental namespace deletion**

1. **Simulate**: `kubectl delete namespace production`
2. **Restore**: 
   ```bash
   velero restore create --from-backup BACKUP_NAME
   ```
3. **Verify**: Use the `validate-restore.sh` script to verify deployments, services, configmaps, and secrets.
4. **Target RTO**: < 10 minutes

## AWS Verification
Verify S3 backup objects exist:
```bash
aws s3 ls s3://velero-backup-20260524124012657700000006/backups/BACKUP_NAME/
```
