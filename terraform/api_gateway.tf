data "google_project" "project" {}

# API Gateway requires these APIs to be enabled
resource "google_project_service" "apigateway_apis" {
  for_each = toset([
    "apigateway.googleapis.com",
    "servicemanagement.googleapis.com",
    "servicecontrol.googleapis.com"
  ])
  service                    = each.key
  disable_dependency_handling = false
}

resource "google_api_gateway_api_config" "api_config" {
  provider      = google-beta
  project       = var.project_id
  api           = google_api_gateway_api.api.api_id
  api_config_id = "app-factory-config-${terraform.workspace}"

  openapi_documents {
    document {
      path     = "spec.yaml"
      contents = base64encode(templatefile("${path.module}/../api-spec.yaml", {
        discovery_cycle_service_url = module.services["discovery-cycle-service"].service.uri
        ai_developer_agent_url      = module.services["ai-developer-agent-service"].service.uri
        cmo_publishing_agent_url    = module.services["cmo-publishing-agent"].service.uri
      }))
    }
  }

  gateway_config {
    backend_config {
      google_service_account = google_service_account.api_gateway_sa.email
    }
  }
  depends_on = [google_project_service.apigateway_apis]
}

resource "google_api_gateway_api" "api" {
  provider   = google-beta
  project    = var.project_id
  api_id     = "app-factory-api-${terraform.workspace}"
  depends_on = [google_project_service.apigateway_apis]
}

resource "google_api_gateway_gateway" "api_gateway" {
  provider      = google-beta
  project       = var.project_id
  region        = var.region
  gateway_id    = "app-factory-gateway-${terraform.workspace}"
  api_config    = google_api_gateway_api_config.api_config.id
  display_name  = "App Factory Gateway (${terraform.workspace})"
  depends_on    = [google_project_service.apigateway_apis]
}