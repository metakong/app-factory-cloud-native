resource "google_cloud_run_v2_service" "service" {
  for_each = var.services
  project  = var.project_id
  name     = "${each.key}-${var.env_suffix}"
  location = var.region

  template {
    service_account = "${each.value.service_account_name}-${var.env_suffix}@${var.project_id}.iam.gserviceaccount.com"
    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/${var.repo_name}/${each.key}"
      dynamic "env" {
        for_each = each.value.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  ingress = each.value.ingress
}