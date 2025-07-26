output "service_urls" {
  description = "The URLs of the deployed Cloud Run services."
  value = {
    for service in google_cloud_run_v2_service.services :
    service.name => service.uri
  }
}

output "apk_bucket_name" {
  description = "The name of the Cloud Storage bucket for APKs."
  value       = google_storage_bucket.apks.name
}