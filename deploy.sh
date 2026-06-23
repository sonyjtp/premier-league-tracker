#!/usr/bin/env bash
# Usage:
#   ./deploy.sh          — deploy both backend and frontend
#   ./deploy.sh backend  — backend only
#   ./deploy.sh frontend — frontend only

set -euo pipefail

REGISTRY="rg.nl-ams.scw.cloud/premierleague"
KUBECONFIG_FILE="kubeconfig-premierleague-cluster.yaml"
NAMESPACE="premierleague"

export KUBECONFIG="$KUBECONFIG_FILE"

TARGET="${1:-both}"

deploy_backend() {
  echo "==> Building and pushing backend (linux/amd64)..."
  docker buildx build --platform linux/amd64 \
    -t "$REGISTRY/pl-backend:latest" --push ./backend
  echo "==> Restarting backend deployment..."
  kubectl rollout restart deployment/backend -n "$NAMESPACE"
  kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=120s
  echo "==> Backend deployed."
}

deploy_frontend() {
  echo "==> Building and pushing frontend (linux/amd64)..."
  docker buildx build --platform linux/amd64 \
    -t "$REGISTRY/pl-frontend:latest" --push ./frontend
  echo "==> Restarting frontend deployment..."
  kubectl rollout restart deployment/frontend -n "$NAMESPACE"
  kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=120s
  echo "==> Frontend deployed."
}

case "$TARGET" in
  backend)  deploy_backend ;;
  frontend) deploy_frontend ;;
  both)     deploy_backend && deploy_frontend ;;
  *)        echo "Usage: ./deploy.sh [backend|frontend|both]" && exit 1 ;;
esac

echo ""
echo "Done. Live at https://thesouthstandlens.fhlcrab32.com"
