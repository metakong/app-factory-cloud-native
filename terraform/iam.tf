# Service Accounts for each microservice
resource "google_service_account" "discovery_cycle_sa" {
  account_id   = "discovery-cycle-sa"
  display_name = "Discovery Cycle Service Account"
}

resource "google_service_account" "cso_vetting_sa" {
  account_id   = "cso-vetting-sa"
  display_name = "CSO Vetting Service Account"
}

resource "google_service_account" "cpo_analysis_sa" {
  account_id   = "cpo-analysis-sa"
  display_name = "CPO Analysis Service Account"
}

resource "google_service_account" "ai_developer_agent_sa" {
  account_id   = "ai-developer-agent-sa"
  display_name = "AI Developer Agent Service Account"
}

resource "google_service_account" "cmo_publishing_agent_sa" {
  account_id   = "cmo-publishing-agent-sa"
  display_name = "CMO Publishing Agent Service Account"
}

resource "google_service_account" "api_gateway_sa" {
  account_id   = "api-gateway-sa"
  display_name = "API Gateway Service Account"
}

# Common IAM Bindings
locals {
  service_accounts = toset([
    google_service_account.discovery_cycle_sa.email,
    google_service_account.cso_vetting_sa.email,
    google_service_account.cpo_analysis_sa.email,
    google_service_account.ai_developer_agent_sa.email,
    google_service_account.cmo_publishing_agent_sa.email,
  ])
}

resource "google_project_iam_member" "secret_accessor" {
  for_each = local.service_accounts
  project  = var.project_id
  role     = "roles/secretmanager.secretAccessor"
  member   = "serviceAccount:${each.value}"
}

resource "google_project_iam_member" "datastore_user" {
  for_each = local.service_accounts
  project  = var.project_id
  role     = "roles/datastore.user"
  member   = "serviceAccount:${each.value}"
}

# Specific IAM Bindings
resource "google_project_iam_member" "ai_platform_user_cpo" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cpo_analysis_sa.email}"
}

resource "google_project_iam_member" "ai_platform_user_dev" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}

resource "google_project_iam_member" "cloudbuild_editor_dev" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}

resource "google_project_iam_member" "storage_admin_dev" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}