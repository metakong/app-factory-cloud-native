# [cite_start]IAM bindings based on the definitive matrix in the readiness report. [cite: 29, 116]
# This ensures each service has only the permissions it absolutely needs.

locals {
  project_number = data.google_project.project.number
  cloud_build_sa = "serviceAccount:${local.project_number}@cloudbuild.gserviceaccount.com"

  # List of secrets each service needs access to
  secrets_map = {
    discovery_cycle_sa      = []
    cso_vetting_sa          = []
    cpo_analysis_sa         = ["gemini-api-key"]
    ai_developer_agent_sa   = ["gemini-api-key", "github-token"]
    cmo_publishing_agent_sa = ["google-play-api-key"]
  }
}

data "google_project" "project" {}

# [cite_start]1. Cloud Build Service Account Permissions (Least Privilege) [cite: 83]
# --------------------------------------------------------------------
# Allows Cloud Build to manage its own builds
resource "google_project_iam_member" "cloudbuild_builds_editor" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = local.cloud_build_sa
}

# Allows Cloud Build to push container images
resource "google_project_iam_member" "cloudbuild_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = local.cloud_build_sa
}

# Allows Cloud Build to read/write Terraform state
resource "google_storage_bucket_iam_member" "cloudbuild_tfstate_admin" {
  bucket = google_storage_bucket.tf_state.name
  role   = "roles/storage.objectAdmin"
  member = local.cloud_build_sa
}

# Allows Cloud Build to impersonate microservice SAs for deployment
resource "google_service_account_iam_member" "cloudbuild_impersonator" {
  for_each = {
    "discovery-cycle"      = google_service_account.discovery_cycle_sa.email
    "cso-vetting"          = google_service_account.cso_vetting_sa.email
    "cpo-analysis"         = google_service_account.cpo_analysis_sa.email
    "ai-developer-agent"   = google_service_account.ai_developer_agent_sa.email
    "cmo-publishing-agent" = google_service_account.cmo_publishing_agent_sa.email
    "ceo-dashboard"        = google_service_account.ceo_dashboard_sa.email
  }
  service_account_id = "projects/${var.project_id}/serviceAccounts/${each.value}"
  [cite_start]role               = "roles/iam.serviceAccountUser" # Can impersonate, not manage SAs [cite: 86]
  member             = local.cloud_build_sa
}


# 2. Microservice Permissions
# --------------------------------------------------------------------

# Common roles: Firestore access for all services
resource "google_project_iam_member" "datastore_user" {
  for_each = {
    "discovery-cycle"      = google_service_account.discovery_cycle_sa.email
    "cso-vetting"          = google_service_account.cso_vetting_sa.email
    "cpo-analysis"         = google_service_account.cpo_analysis_sa.email
    "ai-developer-agent"   = google_service_account.ai_developer_agent_sa.email
    "cmo-publishing-agent" = google_service_account.cmo_publishing_agent_sa.email
  }
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${each.value}"
}

# Common roles: Secret Manager access for specified secrets
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  for_each = { for sa, secrets in local.secrets_map :
    for secret in secrets :
  "${sa}-${secret}" => { sa_email = google_service_account[sa].email, secret_id = secret } }

  project   = var.project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value.sa_email}"
}

# AI Platform User for services calling Gemini
resource "google_project_iam_member" "aiplatform_user" {
  for_each = toset([
    google_service_account.cpo_analysis_sa.email,
    google_service_account.ai_developer_agent_sa.email
  ])
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${each.value}"
}

# Run Invoker permissions for service-to-service/job invocations
resource "google_cloud_run_v2_job_iam_member" "web_scraper_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.jobs["web-scraper-tool"].job.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.discovery_cycle_sa.email}"
}

resource "google_cloud_run_v2_job_iam_member" "play_publisher_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.jobs["play-publisher-tool"].job.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cmo_publishing_agent_sa.email}"
}

resource "google_cloud_run_v2_service_iam_member" "cpo_analysis_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.services["cpo-analysis-service"].service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cso_vetting_sa.email}"
}

# AI Developer Agent specific permissions
resource "google_storage_bucket_iam_member" "ai_dev_apk_bucket_admin" {
  bucket = google_storage_bucket.apks.name
  role   = "roles/storage.objectAdmin" # To write APKs
  member = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}

resource "google_project_iam_member" "ai_dev_builds_editor" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor" # To trigger app-specific builds
  member  = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}

resource "google_service_account_iam_member" "ai_dev_self_token_creator" {
  service_account_id = google_service_account.ai_developer_agent_sa.name
  [cite_start]role               = "roles/iam.serviceAccountTokenCreator" # To create signed URLs [cite: 106]
  member             = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}

# CEO Dashboard specific permissions
resource "google_project_iam_member" "ceo_dashboard_gateway_invoker" {
  project = var.project_id
  role    = "roles/apigateway.invoker"
  member  = "serviceAccount:${google_service_account.ceo_dashboard_sa.email}"
}