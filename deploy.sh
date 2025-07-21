#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

ENV_SUFFIX="$1"
REGION="us-central1"
PROJECT_ID="app-factory-v2"
REPO="app-factory-repo"

echo "--- Starting Deployment for environment: $ENV_SUFFIX ---"
ENV_VARS="GCP_PROJECT=$PROJECT_ID,AI_DEVELOPER_AGENT_SERVICE_URL=https://ai-developer-agent-service-${ENV_SUFFIX}-515413116650.us-central1.run.app,CMO_PUBLISHING_AGENT_SERVICE_URL=https://cmo-publishing-agent-${ENV_SUFFIX}-515413116650.us-central1.run.app,CPO_ANALYSIS_SERVICE_URL=https://cpo-analysis-service-${ENV_SUFFIX}-515413116650.us-central1.run.app,DISCOVERY_CYCLE_SERVICE_URL=https://discovery-cycle-service-${ENV_SUFFIX}-515413116650.us-central1.run.app,CSO_VETTING_SERVICE_URL=https://cso-vetting-service-${ENV_SUFFIX}-515413116650.us-central1.run.app"

echo "Deploying CEO Dashboard..."
gcloud run deploy ceo-dashboard \
    --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/ceo-dashboard" \
    --region="$REGION" \
    --platform=managed \
    --ingress=all \
    --port=80 \
    --allow-unauthenticated \
    --quiet

echo "Deploying internal services..."
# These services are only called by other services and remain internal
gcloud run deploy cso-vetting-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cso-vetting-service" --region="$REGION" --platform=managed --ingress=internal --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy ai-developer-agent-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/ai-developer-agent-service" --region="$REGION" --platform=managed --ingress=all --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy cmo-publishing-agent --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cmo-publishing-agent" --region="$REGION" --platform=managed --ingress=all --set-env-vars="$ENV_VARS" --quiet
gcloud run deploy cpo-analysis-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/cpo-analysis-service" --region="$REGION" --platform=managed --ingress=all --set-env-vars="$ENV_VARS" --quiet

echo "Deploying gateway-accessible service..."
# This service is called by the API Gateway and MUST allow all traffic, protected by IAM.
gcloud run deploy discovery-cycle-service --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/discovery-cycle-service" --region="$REGION" --platform=managed --ingress=all --set-env-vars="$ENV_VARS" --quiet

echo "Deploying jobs..."
gcloud run jobs deploy web-scraper-tool --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/web-scraper-tool" --region="$REGION" --quiet
gcloud run jobs deploy play-publisher-tool --image="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/play-publisher-tool" --region="$REGION" --quiet

echo "--- Deployment finished successfully. ---"