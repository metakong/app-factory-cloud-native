variable "project_id" { type = string }
variable "region" { type = string }
variable "env_suffix" { type = string }
variable "repo_name" { type = string }
variable "services" {
  type = map(object({
    service_account_name = string
    ingress              = string
    secrets              = map(string)
  }))
}