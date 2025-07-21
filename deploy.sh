#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# The _ENV_SUFFIX is passed in from the Cloud Build trigger.
ENV_SUFFIX="$1"
REGION="us-central1"
PROJECT_ID="app-factory-v2"
REPO="app-factory-repo"

echo "--- Starting Production Deployment for environment: $ENV_SUFFIX ---"

# Construct the full environment variables string to be passed to each service.
# Cloud Run automatically provides service URLs to other services in the same project,
# so manually constructing and passing them is not required for service discovery.
# We will pass only the GCP_PROJECT for now, which is used by shared/gcp_client.py.
ENV_VARS="GCP_PROJECT=$PROJECT_ID"

# Deploy all services with internal-only ingress for security.
echo "Deploying services..."
gcloud run deploy cso-vetting-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cso-vetting-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS"
gcloud run deploy ai-developer-agent-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/ai-developer-agent-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS"
gcloud run deploy cmo-publishing-agent --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cmo-publishing-agent" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS"
gcloud run deploy cpo-analysis-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cpo-analysis-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS"
gcloud run deploy discovery-cycle-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/discovery-cycle-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS"

# Deploy the tools as Cloud Run Jobs.
echo "Deploying jobs..."
gcloud run jobs deploy web-scraper-tool --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/web-scraper-tool" --region="$REGION"
gcloud run jobs deploy play-publisher-tool --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/play-publisher-tool" --region="$REGION"

echo "--- Production Deployment finished successfully. ---"