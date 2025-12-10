# Google Cloud Run Deployment Script for PowerShell
# This script builds and deploys the Docker image to Google Cloud Run

$ErrorActionPreference = "Stop"

# Configuration - Update these variables
$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "your-project-id" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$SERVICE_NAME = if ($env:SERVICE_NAME) { $env:SERVICE_NAME } else { "vtuhub-api" }
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
$DOCKERFILE = if ($env:DOCKERFILE) { $env:DOCKERFILE } else { "Dockerfile.cpu" }

Write-Host "[*] Starting deployment to Google Cloud Run" -ForegroundColor Green
Write-Host "Project ID: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host "Service Name: $SERVICE_NAME"
Write-Host "Image: $IMAGE_NAME"
Write-Host "Dockerfile: $DOCKERFILE"

# Check if gcloud is installed
try {
    gcloud --version | Out-Null
}
catch {
    Write-Host "[ERROR] gcloud CLI is not installed" -ForegroundColor Red
    Write-Host "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Check if docker is installed
try {
    docker --version | Out-Null
}
catch {
    Write-Host "[ERROR] Docker is not installed" -ForegroundColor Red
    exit 1
}

# Authenticate with Google Cloud
Write-Host "[1/5] Authenticating with Google Cloud..." -ForegroundColor Yellow
gcloud auth configure-docker

# Set the project
Write-Host "[2/5] Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Build the Docker image
Write-Host "[3/5] Building Docker image..." -ForegroundColor Yellow
docker build -f $DOCKERFILE -t "${IMAGE_NAME}:latest" .

# Push the image to Google Container Registry
Write-Host "[4/5] Pushing image to GCR..." -ForegroundColor Yellow
docker push "${IMAGE_NAME}:latest"

# Deploy to Cloud Run
Write-Host "[5/5] Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image "${IMAGE_NAME}:latest" `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --set-env-vars "PYTHONUNBUFFERED=1,HF_HUB_DISABLE_SYMLINKS_WARNING=1"

Write-Host "[SUCCESS] Deployment complete!" -ForegroundColor Green
Write-Host "Getting service URL..." -ForegroundColor Yellow
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'

