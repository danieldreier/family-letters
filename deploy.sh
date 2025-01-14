#!/bin/bash
set -euo pipefail

# Configuration
PROJECT_ID="family-letters-447801"
REGION="us-central1"
SERVICE_NAME="family-letters-archive"
GCS_BUCKET_NAME="family-letters-dev"

# Ensure we're authenticated and using the right project
echo "🔐 Verifying gcloud authentication..."
gcloud config set project $PROJECT_ID

# Build and deploy using Cloud Build
echo "🏗️ Building and deploying using Cloud Build..."
gcloud builds submit --substitutions=_GCS_BUCKET_NAME=$GCS_BUCKET_NAME

# Make the service public (if not already)
echo "🌍 Ensuring the service is publicly accessible..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --region=$REGION

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')
echo "✨ Deployment complete!"
echo "🌐 Your service is available at: $SERVICE_URL"
