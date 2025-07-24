variable "project_id" { type = string }
variable "region" { type = string }
variable "env_suffix" { type = string }
variable "repo_name" { type = string }
variable "jobs" {
  type = map(object({
    service_account_name = string
    timeout              = string
  }))
}