variable "name" {
  type        = string
  description = "The name of the Cloud Run service."
}

variable "location" {
  type        = string
  description = "The GCP region for the service."
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
  description = "The service account email for the service."
}

variable "container_port" {
  type        = number
  description = "The port the container listens on."
}

variable "ingress_setting" {
  type        = string
  description = "The ingress traffic setting."
}

variable "is_public" {
  type        = bool
  description = "Whether the service should be publicly accessible."
  default     = false
}

variable "env_vars" {
  type        = map(string)
  description = "A map of environment variables for the service."
  default     = {}
}