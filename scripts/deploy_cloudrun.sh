#!/usr/bin/env bash
# deploy_cloudrun.sh
# Deploys PortfolioX to Google Cloud Run (free tier: 2M requests/month)
# Run once to deploy, then run deploy_and_benchmark.sh

set -euo pipefail

PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"
SERVICE_NAME="portfoliox"

if [[ -z "$PROJECT_ID" ]]; then
    echo "Usage: $0 <gcp-project-id> [region]"
    echo "Example: $0 my-gcp-project-123 us-central1"
    echo ""
    echo "Prerequisites:"
    echo "  1. gcloud auth login && gcloud config set project \$PROJECT_ID"
    echo "  2. Enable APIs: gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com"
    echo "  3. Create secrets in Secret Manager (or use --set-env-vars below)"
    exit 1
fi

echo "=== Deploying PortfolioX to Cloud Run ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Build and deploy from GHCR (your Release workflow already pushed there)
IMAGE="ghcr.io/atharva486/portfoliox:latest"

gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --port=8000 \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --set-env-vars="PORT=8000,PYTHONUNBUFFERED=1" \
    --project="$PROJECT_ID"

# Get the URL
URL=$(gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" --project="$PROJECT_ID" --format='value(status.url)')
echo ""
echo "=== Deployed! ==="
echo "URL: $URL"
echo ""
echo "Now set secrets (one-time):"
echo "  gcloud run services update $SERVICE_NAME --region=$REGION --project=$PROJECT_ID \\"
echo "    --set-secrets=DATABASE_URL=projects/$PROJECT_ID/secrets/DATABASE_URL/versions/latest \\"
echo "    --set-secrets=FINNHUB_API_KEY=projects/$PROJECT_ID/secrets/FINHUB_API_KEY/versions/latest \\"
echo "    --set-secrets=GEMINI_API_KEY=projects/$PROJECT_ID/secrets/GEMINI_API_KEY/versions/latest"
echo ""
echo "Or use --set-env-vars for quick test (not recommended for production):"
echo "  gcloud run services update $SERVICE_NAME --region=$REGION --project=$PROJECT_ID \\"
echo "    --set-env-vars=DATABASE_URL=...,FINNHUB_API_KEY=...,GEMINI_API_KEY=..."
echo ""
echo "Then run benchmark:"
echo "  ./scripts/deploy_and_benchmark.sh $URL"