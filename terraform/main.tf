terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

data "google_project" "project" {}

locals {
  services = {
    "ceo-dashboard" = {
      service_account = google_service_account.ceo_dashboard_sa.email
      container_port  = 80
      ingress         = "INGRESS_TRAFFIC_INTERNAL_AND_CLOUD_LOAD_BALANCING"
      is_public       = true # Special case handled by IAP
      env_vars        = {}
    },
    "discovery-cycle-service" = {
      service_account = google_service_account.discovery_cycle_sa.email
      container_port  = 8080
      ingress         = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      is_public       = false
      env_vars = {
        GCP_PROJECT          = var.project_id
        WEB_SCRAPER_JOB_NAME = module.jobs["web-scraper-tool"].job.id
      }
    },
    "cso-vetting-service" = {
      service_account = google_service_account.cso_vetting_sa.email
      container_port  = 8080
      ingress         = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      is_public       = false
      env_vars = {
        GCP_PROJECT              = var.project_id
        CPO_ANALYSIS_SERVICE_URL = module.services["cpo-analysis-service"].service.uri
      }
    },
    "cpo-analysis-service" = {
      service_account = google_service_account.cpo_analysis_sa.email
      container_port  = 8080
      ingress         = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      is_public       = false
      env_vars = {
        GCP_PROJECT = var.project_id
      }
    },
    "ai-developer-agent-service" = {
      service_account = google_service_account.ai_developer_agent_sa.email
      container_port  = 8080
      ingress         = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      is_public       = false
      env_vars = {
        GCP_PROJECT     = var.project_id
        APK_BUCKET_NAME = google_storage_bucket.apks.name
      }
    },
    "cmo-publishing-agent" = {
      service_account = google_service_account.cmo_publishing_agent_sa.email
      container_port  = 8080
      ingress         = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      is_public       = false
      env_vars = {
        GCP_PROJECT        = var.project_id
        PUBLISHER_JOB_NAME = module.jobs["play-publisher-tool"].job.id
      }
    }
  }

  jobs = {
    "web-scraper-tool" = {
      service_account = google_service_account.discovery_cycle_sa.email
      env_vars = {
        GCP_PROJECT = var.project_id
      }
    },
    "play-publisher-tool" = {
      service_account = google_service_account.cmo_publishing_agent_sa.email
      env_vars = {
        GCP_PROJECT     = var.project_id
        APK_BUCKET_NAME = google_storage_bucket.apks.name
      }
    }
  }
}

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