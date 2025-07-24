# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Configure the Terraform backend to store state in GCS
terraform {
  backend "gcs" {}
}

# Enable necessary Google Cloud APIs
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
  service                    = each.key
  disable_dependency_violation = true
  project                    = var.project_id
}

# Create the Artifact Registry for Docker images
resource "google_artifact_registry_repository" "repo" {
  project       = var.project_id
  location      = var.region
  repository_id = "app-factory-repo"
  description   = "Docker repository for App Factory V2"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}

# CEO Dashboard (Frontend)
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

  # Allow public access to the dashboard
  iam_bindings {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }

  depends_on = [google_project_service.apis, google_artifact_registry_repository.repo]
}


# Define all backend services
module "app_services" {
  source = "./modules/cloud_run_service"
  services = {
    "discovery-cycle-service" = {
      service_account_name = "discovery-cycle-sa"
      ingress              = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      secrets              = {}
    },
    "cso-vetting-service" = {
      service_account_name = "cso-vetting-sa"
      ingress              = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      secrets              = {}
    },
    "cpo-analysis-service" = {
      service_account_name = "cpo-analysis-sa"
      ingress              = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      secrets              = {}
    },
    "ai-developer-agent-service" = {
      service_account_name = "ai-developer-agent-sa"
      ingress              = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      secrets = {
        GEMINI_API_KEY = "gemini-api-key"
      }
    },
    "cmo-publishing-agent" = {
      service_account_name = "cmo-publishing-agent-sa"
      ingress              = "INGRESS_TRAFFIC_INTERNAL_ONLY"
      secrets = {
        GOOGLE_PLAY_API_KEY = "google-play-api-key"
      }
    }
  }

  project_id = var.project_id
  region     = var.region
  env_suffix = var.env_suffix
  repo_name  = google_artifact_registry_repository.repo.repository_id

  depends_on = [
    module.iam_service_accounts,
    module.secrets,
    google_project_service.apis,
    google_artifact_registry_repository.repo
  ]
}

# Define all backend jobs
module "app_jobs" {
  source = "./modules/cloud_run_job"
  jobs = {
    "web-scraper-tool" = {
      service_account_name = "discovery-cycle-sa" # Re-using SA for simplicity
      timeout              = "3600s"
    },
    "play-publisher-tool" = {
      service_account_name = "cmo-publishing-agent-sa" # Re-using SA
      timeout              = "3600s"
    }
  }

  project_id = var.project_id
  region     = var.region
  env_suffix = var.env_suffix
  repo_name  = google_artifact_registry_repository.repo.repository_id

  depends_on = [
    module.iam_service_accounts,
    google_project_service.apis,
    google_artifact_registry_repository.repo
  ]
}