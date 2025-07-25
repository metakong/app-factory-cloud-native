locals {
  project_number = data.google_project.project.number
  cloud_build_sa = "serviceAccount:${local.project_number}@cloudbuild.gserviceaccount.com"

  secrets_map = {
    "discovery_cycle_sa"      = ["reddit-app-credentials"],
    "cpo_analysis_sa"         = ["gemini-api-key"],
    "ai_developer_agent_sa"   = ["gemini-api-key", "github-token"],
    "cmo_publishing_agent_sa" = ["google-play-api-key"]
  }

  flat_secret_bindings = flatten([
    for sa_name, secret_list in local.secrets_map : [
      for secret_id in secret_list : {
        sa_email  = google_service_account[sa_name].email
        secret_id = secret_id
      }
    ]
  ])
}

resource "google_project_iam_member" "cloudbuild_builds_editor" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = local.cloud_build_sa
}

resource "google_project_iam_member" "cloudbuild_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = local.cloud_build_sa
}

resource "google_storage_bucket_iam_member" "cloudbuild_tfstate_admin" {
  bucket = google_storage_bucket.tf_state.name
  role   = "roles/storage.objectAdmin"
  member = local.cloud_build_sa
}

resource "google_service_account_iam_member" "cloudbuild_impersonator" {
  for_each = toset([
    google_service_account.discovery_cycle_sa.name,
    google_service_account.cso_vetting_sa.name,
    google_service_account.cpo_analysis_sa.name,
    google_service_account.ai_developer_agent_sa.name,
    google_service_account.cmo_publishing_agent_sa.name,
    google_service_account.ceo_dashboard_sa.name
  ])
  service_account_id = each.value
  role               = "roles/iam.serviceAccountUser"
  member             = local.cloud_build_sa
}

resource "google_project_iam_member" "datastore_user" {
  for_each = toset([
    google_service_account.discovery_cycle_sa.email,
    google_service_account.cso_vetting_sa.email,
    google_service_account.cpo_analysis_sa.email,
    google_service_account.ai_developer_agent_sa.email,
    google_service_account.cmo_publishing_agent_sa.email
  ])
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${each.value}"
}

resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  for_each = {
    for binding in local.flat_secret_bindings : "${binding.sa_email}-${binding.secret_id}" => binding
  }
  project   = var.project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value.sa_email}"
}

resource "google_project_iam_member" "aiplatform_user" {
  for_each = toset([
    google_service_account.cpo_analysis_sa.email,
    google_service_account.ai_developer_agent_sa.email
  ])
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${each.value}"
}

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

resource "google_storage_bucket_iam_member" "ai_dev_apk_bucket_admin" {
  bucket = google_storage_bucket.apks.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}

resource "google_project_iam_member" "ai_dev_builds_editor" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}

resource "google_service_account_iam_member" "ai_dev_self_token_creator" {
  service_account_id = google_service_account.ai_developer_agent_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.ai_developer_agent_sa.email}"
}

resource "google_project_iam_member" "ceo_dashboard_gateway_invoker" {
  project = var.project_id
  role    = "roles/apigateway.invoker"
  member  = "serviceAccount:${google_service_account.ceo_dashboard_sa.email}"
}