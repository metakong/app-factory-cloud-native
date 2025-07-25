output "ceo_dashboard_url" {
  description = "The URL for the CEO Dashboard, secured by IAP."
  value       = "https://${var.domain}"
}

output "load_balancer_ip" {
  description = "The external IP address of the load balancer."
  value       = google_compute_global_address.lb_ip.address
}

output "api_gateway_url" {
  description = "The URL of the API Gateway."
  value       = google_api_gateway_gateway.api_gateway.default_hostname
}