output "ceo_dashboard_url" {
  description = "The secure, IAP-protected URL for the CEO Dashboard."
  value       = module.iac.load_balancer_ip
}

output "api_gateway_url" {
  description = "The URL of the API Gateway."
  value       = "https://${module.api_gateway.gateway.default_hostname}"
}

output "cloud_run_service_urls" {
  description = "The URIs of the deployed Cloud Run services."
  value = { for name, service in module.services : name => service.service.uri }
}