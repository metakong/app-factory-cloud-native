variable "project_id" {
  description = "The Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "The Google Cloud region for deploying resources."
  type        = string
  default     = "us-central1"
}

variable "artifact_repo_name" {
  description = "The name of the Artifact Registry repository."
  type        = string
  default     = "app-factory-repo"
}

variable "ceo_email" {
  description = "The email address of the CEO for IAP access."
  type        = string
  default     = "ceo@example.com"
}

variable "iap_domain" {
  description = "The domain name to use for the IAP-protected CEO Dashboard."
  type        = string
}