resource "google_api_gateway_api" "api" {
  project = var.project_id
  api_id  = "app-factory-gateway-${var.env_suffix}"
}

resource "google_api_gateway_api_config" "api_config" {
  project      = var.project_id
  api          = google_api_gateway_api.api.api_id
  api_config_id = "app-factory-config"

  openapi_documents {
    document {
      path     = "api-spec.yaml"
      contents = base64encode(templatefile("${path.module}/../api-spec.yaml.tftpl", {
        discovery_cycle_service_url = module.app_services.service_urls["discovery-cycle-service"],
        ai_developer_agent_service_url = module.app_services.service_urls["ai-developer-agent-service"],
        cmo_publishing_agent_url = module.app_services.service_urls["cmo-publishing-agent"]
      }))
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_api_gateway_gateway" "gateway" {
  project       = var.project_id
  region        = var.region
  gateway_id    = "app-factory-gateway-${var.env_suffix}"
  api_config    = google_api_gateway_api_config.api_config.id
  display_name  = "App Factory Gateway (${var.env_suffix})"
}