#!/bin/bash
set -euo pipefail

# Automated deployment rollback script
# Usage: ./rollback_deployment.sh <environment> <previous_version>

ENVIRONMENT="${1:-staging}"
PREVIOUS_VERSION="${2:-}"
NAMESPACE="mlsdm"

echo "=== ML-SDM Deployment Rollback ==="
echo "Environment: $ENVIRONMENT"
echo "Namespace: $NAMESPACE"
echo "Previous version: ${PREVIOUS_VERSION:-auto-detect}"

# Validate kubectl access
if ! kubectl get ns "$NAMESPACE" &>/dev/null; then
    echo "ERROR: Cannot access namespace $NAMESPACE"
    exit 1
fi

# Get deployment name
DEPLOYMENT="mlsdm-neuro-engine"

CURRENT_REVISION=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
if [ -z "$CURRENT_REVISION" ] || ! [[ "$CURRENT_REVISION" =~ ^[0-9]+$ ]]; then
    echo "ERROR: Unable to determine current revision for $DEPLOYMENT"
    exit 1
fi

# Auto-detect previous version if not provided
if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Auto-detecting previous version..."
    PREVIOUS_VERSION=$((CURRENT_REVISION - 1))
    if [ "$PREVIOUS_VERSION" -lt 1 ]; then
        echo "ERROR: No previous revision found for rollback"
        exit 1
    fi
    echo "Detected revision: $PREVIOUS_VERSION"
fi

# Confirm rollback
echo ""
echo "⚠️  WARNING: About to rollback $DEPLOYMENT"
echo "This will revert to revision: $PREVIOUS_VERSION"

if [ "$ENVIRONMENT" = "production" ]; then
    echo ""
    read -p "Type 'ROLLBACK' to confirm: " CONFIRM
    if [ "$CONFIRM" != "ROLLBACK" ]; then
        echo "Rollback cancelled"
        exit 1
    fi
fi

# Perform rollback
echo ""
echo "Rolling back deployment..."
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE --to-revision="$PREVIOUS_VERSION"

# Wait for rollback to complete
echo "Waiting for rollback to complete..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s

# Verify rollback success
echo ""
echo "Verifying rollback..."

# Check pod status
READY_PODS=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
DESIRED_PODS=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.replicas}')

if [ "$READY_PODS" != "$DESIRED_PODS" ]; then
    echo "ERROR: Rollback incomplete. Ready: $READY_PODS, Desired: $DESIRED_PODS"
    exit 1
fi

# Run smoke tests
echo "Running smoke tests..."
export SMOKE_TEST_URL="http://mlsdm-neuro-engine.$NAMESPACE.svc.cluster.local:8000"

ROLLED_BACK_IMAGE=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}')
EXPECTED_VERSION=$(echo "$ROLLED_BACK_IMAGE" | awk -F':' '{print $NF}')
export EXPECTED_VERSION

if pytest tests/smoke/test_deployment_smoke.py -v --tb=short; then
    echo ""
    echo "✅ Rollback successful!"
    echo "Deployment: $DEPLOYMENT"
    echo "Namespace: $NAMESPACE"
    echo "Revision: $PREVIOUS_VERSION"
    echo "Ready pods: $READY_PODS/$DESIRED_PODS"
    exit 0
else
    echo ""
    echo "❌ Rollback smoke tests FAILED"
    echo "Manual intervention required!"
    exit 1
fi
