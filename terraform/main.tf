terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # [cite_start]The backend is configured via the CI/CD pipeline arguments for flexibility. [cite: 278]
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  # A map of service names to their specific configurations
  services = {
    "ceo-dashboard" = {
      source_path       = "../frontend"
      service_account   = google_service_account.ceo_dashboard_sa.email
      container_port    = 80
      [cite_start]ingress           = "INGRESS_TRAFFIC_INTERNAL_AND_CLOUD_LOAD_BALANCING" # For IAP [cite: 51]
      is_public         = true # Special case handled by IAP
      env_vars          = {}
    }
    "discovery-cycle-service" = {
      source_path       = "./services/discovery_cycle"
      service_account   = google_service_account.discovery_cycle_sa.email
      container_port    = 8080
      [cite_start]ingress           = "INGRESS_TRAFFIC_INTERNAL_ONLY" # Internal only [cite: 38]
      is_public         = false
      env_vars = {
        GCP_PROJECT     = var.project_id
        WEB_SCRAPER_JOB = module.jobs["web-scraper-tool"].job.id
      }
    }
    "cso-vetting-service" = {
      source_path       = "./services/cso_vetting"
      service_account   = google_service_account.cso_vetting_sa.email
      container_port    = 8080
      [cite_start]ingress           = "INGRESS_TRAFFIC_INTERNAL_ONLY" # Internal only [cite: 38]
      is_public         = false
      env_vars = {
        GCP_PROJECT                = var.project_id
        CPO_ANALYSIS_SERVICE_URL   = module.services["cpo-analysis-service"].service.uri
      }
    }
    "cpo-analysis-service" = {
      source_path       = "./services/cpo_analysis"
      service_account   = google_service_account.cpo_analysis_sa.email
      container_port    = 8080
      [cite_start]ingress           = "INGRESS_TRAFFIC_INTERNAL_ONLY" # Internal only [cite: 38]
      is_public         = false
      env_vars = {
        GCP_PROJECT     = var.project_id
      }
    }
    "ai-developer-agent-service" = {
      source_path       = "./services/ai_developer"
      service_account   = google_service_account.ai_developer_agent_sa.email
      container_port    = 8080
      [cite_start]ingress           = "INGRESS_TRAFFIC_INTERNAL_ONLY" # Internal only [cite: 38]
      is_public         = false
      env_vars = {
        GCP_PROJECT     = var.project_id
        [cite_start]APK_BUCKET_NAME = google_storage_bucket.apks.name # Injected dynamically [cite: 114]
      }
    }
    "cmo-publishing-agent" = {
      source_path       = "./services/cmo_publishing"
      service_account   = google_service_account.cmo_publishing_agent_sa.email
      container_port    = 8080
      [cite_start]ingress           = "INGRESS_TRAFFIC_INTERNAL_ONLY" # Internal only [cite: 38]
      is_public         = false
      env_vars = {
        GCP_PROJECT      = var.project_id
        PUBLISHER_JOB_ID = module.jobs["play-publisher-tool"].job.id
      }
    }
  }

  jobs = {
    "web-scraper-tool" = {
      source_path     = "./tools/robust_web_scraper"
      service_account = google_service_account.discovery_cycle_sa.email # Re-uses SA that invokes it
      env_vars = {
        GCP_PROJECT = var.project_id
      }
    }
    "play-publisher-tool" = {
      source_path     = "./tools/google_play_publisher"
      service_account = google_service_account.cmo_publishing_agent_sa.email # Re-uses SA that invokes it
      env_vars = {
        GCP_PROJECT     = var.project_id
        [cite_start]APK_BUCKET_NAME = google_storage_bucket.apks.name # Injected dynamically [cite: 114]
        # IDEA_ID is passed as an override when the job is run
      }
    }
  }
}

# [cite_start]Instantiate all Cloud Run Services using a reusable module [cite: 77]
module "services" {
  source   = "./modules/cloud_run_service"
  for_each = local.services

  name             = each.key
  location         = var.region
  project_id       = var.project_id
  image_url        = "us-central1-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}/${each.key}:latest"
  service_account  = each.value.service_account
  container_port   = each.value.container_port
  ingress_setting  = each.value.ingress
  is_public        = each.value.is_public
  env_vars         = each.value.env_vars
}

# [cite_start]Instantiate all Cloud Run Jobs using a reusable module [cite: 63]
module "jobs" {
  source   = "./modules/cloud_run_job"
  for_each = local.jobs

  name            = each.key
  location        = var.region
  project_id      = var.project_id
  image_url       = "us-central1-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}/${each.key}:latest"
  service_account = each.value.service_account
  env_vars        = each.value.env_vars
}