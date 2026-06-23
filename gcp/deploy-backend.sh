#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# gcp/deploy-backend.sh — Build & deploy the FastAPI backend to Cloud Run
#
# Usage:
#   bash gcp/deploy-backend.sh
#
# Run this for:
#   - First-time deploy
#   - Manual re-deploy without triggering Cloud Build
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID="YOUR_PROJECT_ID"          # ← CHANGE THIS to your GCP project ID
REGION="us-central1"
AR_REPO="whatsapp-agent"
SERVICE_NAME="whatsapp-agent-backend"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/backend"
# ─────────────────────────────────────────────────────────────────────────────

echo "🏗️  Building backend Docker image..."
docker build \
  -t "${IMAGE}:latest" \
  ./backend

echo ""
echo "📤 Pushing image to Artifact Registry..."
docker push "${IMAGE}:latest"

echo ""
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}:latest" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --min-instances=0 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --concurrency=80 \
  --set-env-vars="MONGO_DB_NAME=whatsapp_agent,APP_ENV=production" \
  --set-secrets="MONGO_URI=MONGO_URI:latest,\
GEMINI_API_KEY=GEMINI_API_KEY:latest,\
TWILIO_ACCOUNT_SID=TWILIO_ACCOUNT_SID:latest,\
TWILIO_AUTH_TOKEN=TWILIO_AUTH_TOKEN:latest,\
TWILIO_WHATSAPP_NUMBER_TENANT_A=TWILIO_WHATSAPP_NUMBER_TENANT_A:latest,\
TWILIO_WHATSAPP_NUMBER_TENANT_B=TWILIO_WHATSAPP_NUMBER_TENANT_B:latest" \
  --project="${PROJECT_ID}"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Backend deployed!"
echo ""
BACKEND_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")
echo "🌐 Backend URL: ${BACKEND_URL}"
echo ""
echo "📌 Next steps:"
echo "  1. Copy this URL: ${BACKEND_URL}"
echo "  2. Update _BACKEND_URL in cloudbuild.yaml"
echo "  3. Run: bash gcp/deploy-frontend.sh \"${BACKEND_URL}\""
echo "  4. Configure Meta webhook: ${BACKEND_URL}/api/webhooks/whatsapp"
echo "  5. Test health: curl ${BACKEND_URL}/health"
echo "════════════════════════════════════════════════════════════"
