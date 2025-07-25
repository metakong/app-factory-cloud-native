variable "project_id" { type = string }
variable "region" { type = string }
variable "job_name" { type = string }
variable "env_suffix" { type = string }
variable "artifact_repo_name" { type = string }
variable "service_account" { type = string }
variable "env_vars" { type = map(string) }

resource "google_cloud_run_v2_job" "job" {
  name     = "${var.job_name}-${var.env_suffix}"
  location = var.region
  project  = var.project_id

  template {
    template {
      service_account = var.service_account
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_name}/${var.job_name}"

        dynamic "env" {
          for_each = merge(
            { "GCP_PROJECT" = var.project_id },
            var.env_vars
          )
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }
}

output "job" {
  value = google_cloud_run_v2_job.job
}