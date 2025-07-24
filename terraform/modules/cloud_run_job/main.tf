resource "google_cloud_run_v2_job" "job" {
  for_each = var.jobs
  project  = var.project_id
  name     = "${each.key}-${var.env_suffix}"
  location = var.region

  template {
    template {
      service_account = "${each.value.service_account_name}-${var.env_suffix}@${var.project_id}.iam.gserviceaccount.com"
      timeout         = each.value.timeout
      containers {
        image = "us-central1-docker.pkg.dev/${var.project_id}/${var.repo_name}/${each.key}"
      }
    }
  }
}