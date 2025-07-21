#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# The first argument to the script is the environment suffix (e.g., "dev", "prod")
ENV_SUFFIX="$1"
REGION="us-central1"
PROJECT_ID="app-factory-v2"
REPO="app-factory-repo"

echo "--- Starting Deployment for environment: $ENV_SUFFIX ---"

# Define Service URLs using the environment suffix.
CSO_VETTING_URL="https://cso-vetting-service-${ENV_SUFFIX}-515413116650.us-central1.run.app"
AI_DEV_URL="https://ai-developer-agent-service-${ENV_SUFFIX}-515413116650.us-central1.run.app"
WEB_SCRAPER_URL="https://web-scraper-tool-${ENV_SUFFIX}-515413116650.us-central1.run.app"
CMO_PUB_URL="https://cmo-publishing-agent-${ENV_SUFFIX}-515413116650.us-central1.run.app"
CPO_ANALYSIS_URL="https://cpo-analysis-service-${ENV_SUFFIX}-515413116650.us-central1.run.app"
DISCOVERY_URL="https://discovery-cycle-service-${ENV_SUFFIX}-515413116650.us-central1.run.app"
PLAY_PUB_URL="https://play-publisher-tool-${ENV_SUFFIX}-515413116650.us-central1.run.app"

# Construct the final environment variables string to be passed to each service.
ENV_VARS="CSO_VETTING_SERVICE_URL=$CSO_VETTING_URL,AI_DEVELOPER_AGENT_SERVICE_URL=$AI_DEV_URL,WEB_SCRAPER_TOOL_URL=$WEB_SCRAPER_URL,CMO_PUBLISHING_AGENT_URL=$CMO_PUB_URL,CPO_ANALYSIS_SERVICE_URL=$CPO_ANALYSIS_URL,DISCOVERY_CYCLE_SERVICE_URL=$DISCOVERY_URL,PLAY_PUBLISHER_TOOL_URL=$PLAY_PUB_URL"

# Deploy all services with internal-only ingress for security and inject environment variables.
echo "Deploying services..."
gcloud run deploy cso-vetting-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cso-vetting-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy ai-developer-agent-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/ai-developer-agent-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy cmo-publishing-agent --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cmo-publishing-agent" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy cpo-analysis-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cpo-analysis-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy discovery-cycle-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/discovery-cycle-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS" --quiet

# Deploy the tools as Cloud Run Jobs.
echo "Deploying jobs..."
gcloud run jobs deploy web-scraper-tool --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/web-scraper-tool" --region="$REGION" --quiet
gcloud run jobs deploy play-publisher-tool --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/play-publisher-tool" --region="$REGION" --quiet

echo "--- Deployment finished successfully. ---"