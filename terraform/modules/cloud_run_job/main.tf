resource "google_cloud_run_v2_job" "default" {
  name     = "${var.name}-${terraform.workspace}"
  location = var.location
  project  = var.project_id

  template {
    template {
      service_account = var.service_account
      containers {
        image = var.image_url
        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }
}