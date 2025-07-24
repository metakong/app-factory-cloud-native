# Create Service Accounts for each microservice
resource "google_service_account" "service_accounts" {
  for_each     = toset(var.service_account_names)
  project      = var.project_id
  account_id   = "${each.key}-${var.env_suffix}"
  display_name = "Service Account for ${each.key} (${var.env_suffix})"
}

# Grant common roles to all service accounts
resource "google_project_iam_member" "secret_accessor" {
  for_each = toset(var.service_account_names)
  project  = var.project_id
  role     = "roles/secretmanager.secretAccessor"
  member   = "serviceAccount:${google_service_account.service_accounts[each.key].email}"
}

resource "google_project_iam_member" "datastore_user" {
  for_each = toset(var.service_account_names)
  project  = var.project_id
  role     = "roles/datastore.user"
  member   = "serviceAccount:${google_service_account.service_accounts[each.key].email}"
}

# Grant specific AI Platform User role
resource "google_project_iam_member" "ai_platform_user" {
  for_each = toset(["cpo-analysis-sa", "ai-developer-agent-sa"])
  project  = var.project_id
  role     = "roles/aiplatform.user"
  member   = "serviceAccount:${google_service_account.service_accounts[each.key].email}"
}

# Grant Cloud Build Editor role to AI Developer Agent
resource "google_project_iam_member" "build_editor" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.service_accounts["ai-developer-agent-sa"].email}"
}

# Grant Run Invoker for jobs
resource "google_cloud_run_v2_job_iam_member" "web_scraper_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.app_jobs.job_names["web-scraper-tool"]
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.service_accounts["discovery-cycle-sa"].email}"
}

resource "google_cloud_run_v2_job_iam_member" "play_publisher_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.app_jobs.job_names["play-publisher-tool"]
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.service_accounts["cmo-publishing-agent-sa"].email}"
}