output "ceo_dashboard_url" {
  description = "The secure, IAP-protected URL for the CEO Dashboard."
  value       = "https://${var.iap_domain}"
}

output "load_balancer_ip" {
  description = "Public IP of the IAP-protected Load Balancer. Point your DNS A record to this."
  value       = module.iac.load_balancer_ip
}

output "api_gateway_url" {
  description = "The URL of the API Gateway."
  value       = module.api_gateway.gateway.default_hostname
}