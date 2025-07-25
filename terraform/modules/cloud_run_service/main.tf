resource "google_cloud_run_v2_service" "default" {
  name     = "${var.name}-${terraform.workspace}"
  location = var.location
  project  = var.project_id

  template {
    service_account = var.service_account
    containers {
      image = var.image_url
      ports {
        container_port = var.container_port
      }
      env {
        name  = "K_SERVICE"
        value = "${var.name}-${terraform.workspace}"
      }
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  ingress = var.ingress_setting

  # Only create the public access policy if explicitly set to public
  # [cite_start]This avoids using allUsers by default, enforcing security. [cite: 41, 42]
  lifecycle {
    ignore_changes = [
      # Ignore changes to annotations, they are often managed by Google.
      "template.annotations",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "public_access" {
  count    = var.is_public ? 1 : 0
  project  = var.project_id
  location = var.location
  service  = google_cloud_run_v2_service.default.name
  policy_data = data.google_iam_policy.public.policy_data
}

data "google_iam_policy" "public" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}