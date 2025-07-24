provider "google" {
  project = var.project_id
  region  = var.region
}

terraform {
  backend "gcs" {}
}

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "firestore.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "apigateway.googleapis.com",
    "servicecontrol.googleapis.com",
    "servicemanagement.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "repo" {
  project       = var.project_id
  location      = var.region
  repository_id = "app-factory-repo"
  description   = "Docker repository for App Factory V2"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_cloud_run_v2_service" "ceo_dashboard" {
  name     = "ceo-dashboard"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/app-factory-repo/ceo-dashboard"
      ports {
        container_port = 80
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [google_project_service.apis, google_artifact_registry_repository.repo]
}

resource "google_cloud_run_service_iam_member" "ceo_dashboard_invoker" {
  location = google_cloud_run_v2_service.ceo_dashboard.location
  project  = google_cloud_run_v2_service.ceo_dashboard.project
  service  = google_cloud_run_v2_service.ceo_dashboard.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

module "app_services" {
  source     = "./modules/cloud_run_service"
  project_id = var.project_id
  region     = var.region
  env_suffix = var.env_suffix
  repo_name  = google_artifact_registry_repository.repo.repository_id
  services = {
    "discovery-cycle-service"    = { service_account_name = "discovery-cycle-sa", ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", secrets = {} },
    "cso-vetting-service"        = { service_account_name = "cso-vetting-sa", ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", secrets = {} },
    "cpo-analysis-service"       = { service_account_name = "cpo-analysis-sa", ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", secrets = {} },
    "ai-developer-agent-service" = { service_account_name = "ai-developer-agent-sa", ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", secrets = { GEMINI_API_KEY = "gemini-api-key" } },
    "cmo-publishing-agent"       = { service_account_name = "cmo-publishing-agent-sa", ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY", secrets = { GOOGLE_PLAY_API_KEY = "google-play-api-key" } }
  }
}

module "app_jobs" {
  source     = "./modules/cloud_run_job"
  project_id = var.project_id
  region     = var.region
  env_suffix = var.env_suffix
  repo_name  = google_artifact_registry_repository.repo.repository_id
  jobs = {
    "web-scraper-tool"    = { service_account_name = "discovery-cycle-sa", timeout = "3600s" },
    "play-publisher-tool" = { service_account_name = "cmo-publishing-agent-sa", timeout = "3600s" }
  }
}