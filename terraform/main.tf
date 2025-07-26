terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.50.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- Cloud Storage Buckets ---
resource "google_storage_bucket" "apks" {
  name          = "${var.project_id}-apks"
  location      = var.region
  force_destroy = true
  public_access_prevention = "enforced"
}

resource "google_storage_bucket" "tf_state" {
  name          = "${var.project_id}-tf-state"
  location      = "US" # Terraform state bucket must be multi-regional
  force_destroy = true
  public_access_prevention = "enforced"
}

# --- Cloud Run Services ---
resource "google_cloud_run_v2_service" "services" {
  for_each = toset(var.services)
  name     = each.key
  location = var.region
  template {
    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/app-factory-repo/${each.key}:latest"
    }
  }
}