variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for resources."
  type        = string
  default     = "us-central1"
}

variable "env_suffix" {
  description = "The environment suffix (e.g., 'dev', 'prod')."
  type        = string
}

variable "service_account_names" {
  description = "A list of service account short names to create."
  type        = list(string)
  default = [
    "discovery-cycle-sa",
    "cso-vetting-sa",
    "cpo-analysis-sa",
    "ai-developer-agent-sa",
    "cmo-publishing-agent-sa"
  ]
}

variable "secret_names" {
  description = "A list of secret IDs that the Cloud Build SA needs to access."
  type        = list(string)
  default = [
    "gemini-api-key",
    "github-token",
    "google-play-api-key",
    "flutter-keystore-jks",
    "flutter-key-properties"
  ]
}