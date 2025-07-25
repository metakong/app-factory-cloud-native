# [cite_start]Bucket for Terraform state - MUST NOT be public. [cite: 14, 15]
resource "google_storage_bucket" "tf_state" {
  name          = "app-factory-v2-tf-state" # Should be globally unique
  location      = "US"
  force_destroy = false

  uniform_bucket_level_access = true
  [cite_start]public_access_prevention    = "enforced" # Critical security setting [cite: 19]

  versioning {
    enabled = true
  }
}

# Bucket for storing generated APKs - MUST NOT be public.
resource "google_storage_bucket" "apks" {
  name          = "app-factory-v2-apks"
  location      = "US-CENTRAL1"
  force_destroy = false

  uniform_bucket_level_access = true
  [cite_start]public_access_prevention    = "enforced" # Critical security setting [cite: 19]
}

# Bucket for Cloud Build logs - MUST NOT be public.
resource "google_storage_bucket" "cloudbuild_logs" {
  name          = "app-factory-v2_cloudbuild"
  location      = "US-CENTRAL1"
  force_destroy = false

  uniform_bucket_level_access = true
  [cite_start]public_access_prevention    = "enforced" # Critical security setting [cite: 19]
}