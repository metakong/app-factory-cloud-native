output "job_names" {
  value = { for k, v in google_cloud_run_v2_job.job : k => v.name }
}