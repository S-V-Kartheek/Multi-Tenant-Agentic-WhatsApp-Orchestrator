$ErrorActionPreference = "Stop"

$PROJECT_ID = "project-f1feb61f-6c71-4181-96c"
$REGION = "us-central1"
$AR_REPO = "whatsapp-agent"

Write-Host "🚀 Setting up GCP project: $PROJECT_ID"
Write-Host "📍 Region: $REGION"
Write-Host ""

# 1. Set active project
Write-Host "▶ Setting active GCP project..."
gcloud config set project $PROJECT_ID

# 2. Enable APIs
Write-Host "▶ Enabling required GCP APIs (this may take 2-3 minutes)..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com --project=$PROJECT_ID
Write-Host "✅ APIs enabled."

# 3. Create Artifact Registry
Write-Host "▶ Creating Artifact Registry Docker repository..."
try {
    gcloud artifacts repositories create $AR_REPO --repository-format=docker --location=$REGION --description="Multi-Tenant WhatsApp Agent Docker images" --project=$PROJECT_ID 2>$null
} catch {
    Write-Host "  (repository already exists, skipping)"
}
Write-Host "✅ Artifact Registry: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"

# 4. Auth docker
Write-Host "▶ Configuring Docker to use Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# 5. Create Secrets
Write-Host "▶ Creating secrets in Secret Manager..."
function Create-Secret {
    param($SecretName, $SecretValue)
    
    $exists = gcloud secrets describe $SecretName --project=$PROJECT_ID 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ⚠️  Secret '$SecretName' already exists — skipping creation."
    } else {
        $SecretValue | gcloud secrets create $SecretName --data-file=- --replication-policy=automatic --project=$PROJECT_ID
        Write-Host "  ✅ Created secret: $SecretName"
    }
}

# (The secrets will be created manually or passed in next)
Write-Host "✅ GCP script ready."
