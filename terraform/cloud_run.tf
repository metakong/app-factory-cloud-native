module "services" {
  source   = "./modules/cloud_run_service"
  for_each = {
    "ceo-dashboard"              = { ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER", service_account = null, env = {} }
    "discovery-cycle-service"    = { ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", service_account = google_service_account.discovery_cycle_sa.email, env = { "WEB_SCRAPER_JOB_NAME" = module.jobs["web-scraper-tool"].job.name } }
    "cso-vetting-service"        = { ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", service_account = google_service_account.cso_vetting_sa.email, env = { "CPO_ANALYSIS_SERVICE_URL" = module.services["cpo-analysis-service"].service.uri } }
    "cpo-analysis-service"       = { ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", service_account = google_service_account.cpo_analysis_sa.email, env = {} }
    "ai-developer-agent-service" = { ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", service_account = google_service_account.ai_developer_agent_sa.email, env = { "APK_BUCKET_NAME" = google_storage_bucket.apks.name } }
    "cmo-publishing-agent"       = { ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", service_account = google_service_account.cmo_publishing_agent_sa.email, env = { "PUBLISHER_JOB_NAME" = module.jobs["play-publisher-tool"].job.name } }
  }

  project_id         = var.project_id
  region             = var.region
  service_name       = each.key
  env_suffix         = terraform.workspace
  artifact_repo_name = var.artifact_repo_name
  ingress_setting    = each.value.ingress
  service_account    = each.value.service_account
  env_vars           = each.value.env
}

module "jobs" {
  source   = "./modules/cloud_run_job"
  for_each = {
    "web-scraper-tool"    = { service_account = google_service_account.discovery_cycle_sa.email, env = {} }
    "play-publisher-tool" = { service_account = google_service_account.cmo_publishing_agent_sa.email, env = { "APK_BUCKET_NAME" = google_storage_bucket.apks.name } }
  }

  project_id         = var.project_id
  region             = var.region
  job_name           = each.key
  env_suffix         = terraform.workspace
  artifact_repo_name = var.artifact_repo_name
  service_account    = each.value.service_account
  env_vars           = each.value.env
}

# Grant invoker permissions between services/jobs
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