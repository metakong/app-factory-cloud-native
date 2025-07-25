# [cite_start]Deploys the API Gateway using a templated OpenAPI spec [cite: 55]

resource "google_project_service" "apigateway" {
  service            = "apigateway.googleapis.com"
  disable_on_destroy = false
}

resource "google_api_gateway_api" "app_factory_api" {
  provider = google-beta
  project  = var.project_id
  api_id   = "app-factory-api"
  depends_on = [
    google_project_service.apigateway
  ]
}

resource "google_api_gateway_api_config" "app_factory_config" {
  provider = google-beta
  project  = var.project_id
  api      = google_api_gateway_api.app_factory_api.api_id
  api_config_id = "app-factory-config-${terraform.workspace}"

  openapi_documents {
    document {
      path     = "api-spec.yaml"
      contents = base64encode(templatefile("${path.module}/api-spec.yaml.tftpl", {
        discovery_cycle_service_url    = module.services["discovery-cycle-service"].service.uri
        ai_developer_agent_service_url = module.services["ai-developer-agent-service"].service.uri
        cmo_publishing_agent_url       = module.services["cmo-publishing-agent"].service.uri
      [cite_start]})) # [cite: 56]
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "google_api_gateway_gateway" "gateway" {
  provider      = google-beta
  project       = var.project_id
  region        = var.region
  gateway_id    = "app-factory-gateway-${terraform.workspace}"
  api_config    = google_api_gateway_api_config.app_factory_config.id
  display_name  = "App Factory Gateway (${terraform.workspace})"
}

module "api_gateway" {
  source = "./" # Assuming the files are in the same directory.
  # Add necessary variables here.
}