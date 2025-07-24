output "gateway_url" {
  description = "The URL of the deployed API Gateway."
  value       = "https://${google_api_gateway_gateway.gateway.default_hostname}"
}

output "ceo_dashboard_url" {
  description = "The URL of the deployed CEO Dashboard."
  value       = google_cloud_run_v2_service.ceo_dashboard.uri
}