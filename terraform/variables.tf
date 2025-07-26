variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for resources."
  type        = string
  default     = "us-central1"
}

variable "services" {
  description = "A list of Cloud Run services to deploy."
  type        = list(string)
  default = [
    "ceo-dashboard",
    "discovery-cycle-service",
    "cpo-analysis-service",
    "cmo-publishing-agent",
    "web-scraper-tool",
    "ai-developer-agent-service",
    "cso-vetting-service",
    "play-publisher-tool"
  ]
}