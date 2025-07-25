variable "name" {
  type        = string
  description = "The name of the Cloud Run job."
}

variable "location" {
  type        = string
  description = "The GCP region for the job."
}

variable "project_id" {
  type        = string
  description = "The GCP project ID."
}

variable "image_url" {
  type        = string
  description = "The full URL of the container image."
}

variable "service_account" {
  type        = string
  description = "The service account email for the job."
}

variable "env_vars" {
  type        = map(string)
  description = "A map of environment variables for the job."
  default     = {}
}