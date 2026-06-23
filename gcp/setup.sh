#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# gcp/setup.sh — One-time GCP project setup for Multi-Tenant WhatsApp Agent
#
# Usage:
#   1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
#   2. Run: gcloud auth login
#   3. Edit PROJECT_ID below
#   4. bash gcp/setup.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID="YOUR_PROJECT_ID"          # ← CHANGE THIS to your GCP project ID
REGION="us-central1"
AR_REPO="whatsapp-agent"
# ─────────────────────────────────────────────────────────────────────────────

echo "🚀 Setting up GCP project: ${PROJECT_ID}"
echo "📍 Region: ${REGION}"
echo ""

# ── 1. Set active project ──────────────────────────────────────────────────
echo "▶ Setting active GCP project..."
gcloud config set project "${PROJECT_ID}"

# ── 2. Enable required APIs ────────────────────────────────────────────────
echo ""
echo "▶ Enabling required GCP APIs (this may take 2-3 minutes)..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --project="${PROJECT_ID}"
echo "✅ APIs enabled."

# ── 3. Create Artifact Registry repository ────────────────────────────────
echo ""
echo "▶ Creating Artifact Registry Docker repository..."
gcloud artifacts repositories create "${AR_REPO}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Multi-Tenant WhatsApp Agent Docker images" \
  --project="${PROJECT_ID}" \
  2>/dev/null || echo "  (repository already exists, skipping)"
echo "✅ Artifact Registry: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"

# ── 4. Configure Docker auth for Artifact Registry ────────────────────────
echo ""
echo "▶ Configuring Docker to use Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ── 5. Create secrets in Secret Manager ───────────────────────────────────
echo ""
echo "▶ Creating secrets in Secret Manager..."
echo "  You will be prompted to enter each secret value."
echo ""

create_secret() {
  local SECRET_NAME="$1"
  local DESCRIPTION="$2"

  if gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "  ⚠️  Secret '${SECRET_NAME}' already exists — skipping creation."
    echo "      To update: echo -n 'newvalue' | gcloud secrets versions add ${SECRET_NAME} --data-file=-"
  else
    echo -n "  Enter value for [${SECRET_NAME}] (${DESCRIPTION}): "
    read -rs SECRET_VALUE
    echo ""
    echo -n "${SECRET_VALUE}" | gcloud secrets create "${SECRET_NAME}" \
      --data-file=- \
      --replication-policy=automatic \
      --project="${PROJECT_ID}"
    echo "  ✅ Created secret: ${SECRET_NAME}"
  fi
}

create_secret "MONGO_URI"                         "MongoDB Atlas connection string"
create_secret "GEMINI_API_KEY"                    "Google Gemini API key (from AI Studio)"
create_secret "TWILIO_ACCOUNT_SID"                "Twilio Account SID (from console.twilio.com)"
create_secret "TWILIO_AUTH_TOKEN"                 "Twilio Auth Token (from console.twilio.com)"
create_secret "TWILIO_WHATSAPP_NUMBER_TENANT_A"   "Twilio WhatsApp number for Tenant A e.g. whatsapp:+14155238886"
create_secret "TWILIO_WHATSAPP_NUMBER_TENANT_B"   "Twilio WhatsApp number for Tenant B (can be same as A in sandbox)"

# ── 6. Grant Cloud Run SA access to secrets ───────────────────────────────
echo ""
echo "▶ Granting Cloud Run service account access to Secret Manager..."

PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
CR_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

SECRETS=(
  MONGO_URI GEMINI_API_KEY
  TWILIO_ACCOUNT_SID TWILIO_AUTH_TOKEN
  TWILIO_WHATSAPP_NUMBER_TENANT_A TWILIO_WHATSAPP_NUMBER_TENANT_B
)

for SECRET in "${SECRETS[@]}"; do
  gcloud secrets add-iam-policy-binding "${SECRET}" \
    --member="serviceAccount:${CR_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="${PROJECT_ID}" \
    --quiet
  echo "  ✅ ${SECRET} → Cloud Run SA"
done

# ── 7. Grant Cloud Build permissions ──────────────────────────────────────
echo ""
echo "▶ Granting Cloud Build service account required roles..."
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/run.admin" --quiet

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/iam.serviceAccountUser" --quiet

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/artifactregistry.writer" --quiet

echo "  ✅ Cloud Build SA has Cloud Run + Artifact Registry access"

# ── Done ──────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ GCP setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run: bash gcp/deploy-backend.sh    ← first backend deploy"
echo "  2. Copy the backend Cloud Run URL"
echo "  3. Run: bash gcp/deploy-frontend.sh   ← deploy frontend"
echo "  4. Paste backend URL into Twilio sandbox webhook config"
echo "  5. Connect GitHub to Cloud Build for auto CI/CD"
echo "════════════════════════════════════════════════════════════"
