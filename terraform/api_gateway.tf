resource "google_compute_global_address" "lb_ip" {
  name = "ceo-dashboard-lb-ip"
}

resource "google_iap_brand" "project_brand" {
  support_email     = var.ceo_email
  application_title = "App Factory CEO Dashboard"
  project           = data.google_project.project.project_id
}

resource "google_iap_client" "project_client" {
  display_name = "CEO Dashboard IAP Client"
  brand        = google_iap_brand.project_brand.name
}

resource "google_compute_region_network_endpoint_group" "serverless_neg" {
  name                  = "ceo-dashboard-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = module.services["ceo-dashboard"].service.name
  }
}

resource "google_compute_backend_service" "backend_service" {
  name                  = "ceo-dashboard-backend"
  protocol              = "HTTP"
  port_name             = "http"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  enable_cdn            = false
  backend {
    group = google_compute_region_network_endpoint_group.serverless_neg.id
  }
  iap {
    oauth2_client_id     = google_iap_client.project_client.client_id
    oauth2_client_secret = google_iap_client.project_client.secret
  }
}

resource "google_compute_url_map" "url_map" {
  name            = "ceo-dashboard-url-map"
  default_service = google_compute_backend_service.backend_service.id
}

resource "google_compute_managed_ssl_certificate" "ssl_cert" {
  name = "ceo-dashboard-ssl-cert"
  managed {
    domains = [var.iap_domain]
  }
}

resource "google_compute_target_https_proxy" "https_proxy" {
  name             = "ceo-dashboard-https-proxy"
  url_map          = google_compute_url_map.url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.ssl_cert.id]
}

resource "google_compute_global_forwarding_rule" "forwarding_rule" {
  name       = "ceo-dashboard-forwarding-rule"
  ip_address = google_compute_global_address.lb_ip.address
  target     = google_compute_target_https_proxy.https_proxy.id
  port_range = "443"
}

resource "google_iap_web_iam_member" "ceo_access" {
  project = var.project_id
  role    = "roles/iap.httpsResourceAccessor"
  member  = var.ceo_email
}