#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# gcp/deploy-frontend.sh — Build & deploy the React frontend to Cloud Run
#
# Usage:
#   bash gcp/deploy-frontend.sh <BACKEND_URL>
#
# Example:
#   bash gcp/deploy-frontend.sh https://whatsapp-agent-backend-xxxx-uc.a.run.app
#
# NOTE: The backend URL is baked into the frontend at build time (Vite env var).
#       Run this AFTER the backend is deployed and you have its Cloud Run URL.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID="YOUR_PROJECT_ID"          # ← CHANGE THIS to your GCP project ID
REGION="us-central1"
AR_REPO="whatsapp-agent"
SERVICE_NAME="whatsapp-agent-frontend"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/frontend"
# ─────────────────────────────────────────────────────────────────────────────

# ── Require backend URL argument ─────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo "❌ Missing backend URL argument."
  echo ""
  echo "Usage: bash gcp/deploy-frontend.sh <BACKEND_URL>"
  echo "Example: bash gcp/deploy-frontend.sh https://whatsapp-agent-backend-xxxx-uc.a.run.app"
  exit 1
fi

BACKEND_URL="$1"
echo "🔗 Backend URL (baked into build): ${BACKEND_URL}"
echo ""

echo "🏗️  Building frontend Docker image with backend URL..."
docker build \
  -t "${IMAGE}:latest" \
  --build-arg "VITE_API_BASE_URL=${BACKEND_URL}" \
  ./frontend

echo ""
echo "📤 Pushing image to Artifact Registry..."
docker push "${IMAGE}:latest"

echo ""
echo "🚀 Deploying frontend to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}:latest" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --min-instances=0 \
  --max-instances=5 \
  --memory=256Mi \
  --cpu=1 \
  --project="${PROJECT_ID}"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Frontend deployed!"
echo ""
FRONTEND_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")
echo "🌐 Frontend URL: ${FRONTEND_URL}"
echo ""
echo "📌 Next steps:"
echo "  1. Open your dashboard: ${FRONTEND_URL}"
echo "  2. Update CORS_ORIGINS in backend with this URL (if needed)"
echo "  3. Connect GitHub → Cloud Build for auto CI/CD"
echo "════════════════════════════════════════════════════════════"
