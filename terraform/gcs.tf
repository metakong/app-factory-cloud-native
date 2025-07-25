resource "google_storage_bucket" "tf_state" {
  name          = "${var.project_id}-tf-state"
  location      = "US"
  force_destroy = false

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_storage_bucket" "apks" {
  name                        = "${var.project_id}-apks"
  location                    = "US-CENTRAL1"
  force_destroy               = false
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
}