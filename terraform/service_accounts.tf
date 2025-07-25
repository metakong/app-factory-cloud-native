resource "google_service_account" "discovery_cycle_sa" {
  account_id   = "discovery-cycle-sa"
  display_name = "Service Account for Discovery Cycle Service"
  project      = var.project_id
}

resource "google_service_account" "cso_vetting_sa" {
  account_id   = "cso-vetting-sa"
  display_name = "Service Account for CSO Vetting Service"
  project      = var.project_id
}

resource "google_service_account" "cpo_analysis_sa" {
  account_id   = "cpo-analysis-sa"
  display_name = "Service Account for CPO Analysis Service"
  project      = var.project_id
}

resource "google_service_account" "ai_developer_agent_sa" {
  account_id   = "ai-developer-agent-sa"
  display_name = "Service Account for AI Developer Service"
  project      = var.project_id
}

resource "google_service_account" "cmo_publishing_agent_sa" {
  account_id   = "cmo-publishing-agent-sa"
  display_name = "Service Account for CMO Publishing Agent Service"
  project      = var.project_id
}

resource "google_service_account" "ceo_dashboard_sa" {
  account_id   = "ceo-dashboard-sa"
  display_name = "Service Account for CEO Dashboard Frontend"
  project      = var.project_id
}