#!/bin/bash
set -euo pipefail # Exit on error, unset variable, pipe failure

# --- Configuration ---
ENV_SUFFIX="$1"
REGION="us-central1"
PROJECT_ID="app-factory-v2"
REPO="app-factory-repo"

# --- Check for required arguments ---
if [ -z "$ENV_SUFFIX" ]; then
  echo "Error: Environment suffix is required. Usage: ./deploy.sh <dev|prod>"
  exit 1
fi

# --- Construct service image URLs ---
CEO_DASHBOARD_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/ceo-dashboard"
CSO_VETTING_SERVICE_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cso-vetting-service"
AI_DEVELOPER_AGENT_SERVICE_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/ai-developer-agent-service"
CMO_PUBLISHING_AGENT_SERVICE_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cmo-publishing-agent"
CPO_ANALYSIS_SERVICE_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cpo-analysis-service"
DISCOVERY_CYCLE_SERVICE_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/discovery-cycle-service"
WEB_SCRAPER_TOOL_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/web-scraper-tool"
PLAY_PUBLISHER_TOOL_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/play-publisher-tool"

# --- Construct environment variables ---
# All backend services need to know the GCP_PROJECT for the gcp_client.
ENV_VARS="GCP_PROJECT=$PROJECT_ID"

echo "--- Starting Deployment for environment: $ENV_SUFFIX ---"

echo "Deploying CEO Dashboard..."
gcloud run deploy ceo-dashboard \
    --image="$CEO_DASHBOARD_IMAGE" \
    --region="$REGION" \
    --platform=managed \
    --ingress=all \
    --port=80 \
    --allow-unauthenticated \
    --quiet

echo "Deploying internal services..."
gcloud run deploy cso-vetting-service --image="$CSO_VETTING_SERVICE_IMAGE" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy ai-developer-agent-service --image="$AI_DEVELOPER_AGENT_SERVICE_IMAGE" --region="$REGION" --platform=managed --ingress=all --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy cmo-publishing-agent --image="$CMO_PUBLISHING_AGENT_SERVICE_IMAGE" --region="$REGION" --platform=managed --ingress=all --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy cpo-analysis-service --image="$CPO_ANALYSIS_SERVICE_IMAGE" --region="$REGION" --platform=managed --ingress=all --set-env-vars="$ENV_VARS" --quiet

echo "Deploying gateway-accessible service..."
gcloud run deploy discovery-cycle-service --image="$DISCOVERY_CYCLE_SERVICE_IMAGE" --region="$REGION" --platform=managed --ingress=all --set-env-vars="$ENV_VARS" --quiet

echo "Deploying jobs..."
gcloud run jobs deploy web-scraper-tool --image="$WEB_SCRAPER_TOOL_IMAGE" --region="$REGION" --quiet
gcloud run jobs deploy play-publisher-tool --image="$PLAY_PUBLISHER_TOOL_IMAGE" --region="$REGION" --quiet

echo "--- Deployment finished successfully. ---"