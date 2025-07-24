# This module assumes secrets are pre-created in Secret Manager.
# It grants the Cloud Build service account access to them.
data "google_project" "project" {
  project_id = var.project_id
}

resource "google_secret_manager_secret_iam_member" "cloud_build_access" {
  for_each  = toset(var.secret_names)
  project   = var.project_id
  secret_id = each.key
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}