#!/bin/bash
NAMESPACE="production"
EXPECTED_DEPLOYMENTS=1
EXPECTED_SERVICES=1
EXPECTED_CONFIGMAPS=1
EXPECTED_REPLICAS=3

echo "Validating Restored Resources in namespace: $NAMESPACE"

# Check Deployments
ACTUAL_DEPLOYS=$(kubectl get deployment -n $NAMESPACE --no-headers | wc -l)
if [ "$ACTUAL_DEPLOYS" -ne "$EXPECTED_DEPLOYMENTS" ]; then
    echo "FAIL: Expected $EXPECTED_DEPLOYMENTS Deployments, found $ACTUAL_DEPLOYS"
    exit 1
fi

# Check Services
ACTUAL_SVCS=$(kubectl get svc -n $NAMESPACE --no-headers | wc -l)
if [ "$ACTUAL_SVCS" -ne "$EXPECTED_SERVICES" ]; then
    echo "FAIL: Expected $EXPECTED_SERVICES Services, found $ACTUAL_SVCS"
    exit 1
fi

# Hit Actuator Endpoints
PODS=$(kubectl get pods -n $NAMESPACE -l app=my-service -o jsonpath='{.items[*].metadata.name}')
for POD in $PODS; do
    echo "Checking actuator on $POD..."
    STATUS=$(kubectl exec -n $NAMESPACE $POD -- curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/actuator/health)
    if [ "$STATUS" -ne 200 ]; then
        echo "FAIL: Actuator health check failed on $POD (Status: $STATUS)"
        exit 1
    fi
done

echo "SUCCESS: All restored resources validated successfully!"
