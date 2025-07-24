#!/bin/bash
# This script sets up the necessary IAM permissions for the App Factory services.
set -euo pipefail # Exit on error, unset variable, pipe failure

PROJECT_ID="app-factory-v2"
REGION="us-central1"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

echo "Enabling necessary Google Cloud APIs for project: $PROJECT_ID..."
gcloud services enable \
    run.googleapis.com \
    iam.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    --project="$PROJECT_ID"

echo "Creating Artifact Registry repository 'app-factory-repo'..."
gcloud artifacts repositories create app-factory-repo \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker repository for App Factory V2" \
    --project="$PROJECT_ID" || echo "Repository 'app-factory-repo' already exists."

echo "Granting Cloud Build service account permissions..."
CLOUD_BUILD_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin" \
    --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/artifactregistry.writer" \
    --condition=None

echo "Configuring IAM permissions for each microservice..."

SERVICE_ACCOUNTS=(
    "discovery-cycle-sa"
    "cso-vetting-sa"
    "cpo-analysis-sa"
    "ai-developer-agent-sa"
    "cmo-publishing-agent-sa"
    "mcp-gateway-sa"
)

echo "Creating service accounts if they do not exist..."
for SA_NAME in "${SERVICE_ACCOUNTS[@]}"; do
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="$SA_NAME" \
        --project="$PROJECT_ID" || echo "Service account $SA_NAME already exists."
done

# Grant common permissions
for SA_NAME in "${SERVICE_ACCOUNTS[@]}"; do
    SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
    echo "Granting common permissions to $SA_EMAIL..."

    # Permission to access secrets
    gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_EMAIL" --role="roles/secretmanager.secretAccessor" --condition=None
    # Permission to read/write to Firestore
    gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_EMAIL" --role="roles/datastore.user" --condition=None
done

# Grant specific permissions for services that use the Gemini API
echo "Granting AI Platform User role to CPO and AI Developer services..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:cpo-analysis-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user" --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:ai-developer-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user" --condition=None

# Grant specific permissions for services that trigger other services/jobs
echo "Granting invoker and runner permissions..."
gcloud run jobs add-iam-policy-binding web-scraper-tool \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --member="serviceAccount:discovery-cycle-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

gcloud run jobs add-iam-policy-binding play-publisher-tool \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --member="serviceAccount:cmo-publishing-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:ai-developer-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.editor" --condition=None

echo "IAM setup complete."