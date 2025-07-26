variable "project_id" {
  description = "The GCP project ID."
  type        = string
  default     = "app-factory-v2"
}

variable "region" {
  description = "The GCP region for resources."
  type        = string
  default     = "us-central1"
}

variable "artifact_repo_name" {
  description = "The name of the Artifact Registry repository."
  type        = string
  default     = "app-factory-repo"
}

variable "ceo_email" {
  description = "The email address of the CEO for IAP access. Must be prefixed with 'user:'."
  type        = string
  default     = "user:ceo@example.com"
}

variable "domain" {
  description = "The domain name for the CEO dashboard SSL certificate."
  type        = string
  default     = "ceo-dashboard.app-factory.com"
}