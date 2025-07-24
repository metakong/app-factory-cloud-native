# App Factory V2 - Cloud Native (Production Ready)

This repository contains the complete infrastructure-as-code and application source for the App Factory V2 project. This version has been refactored for production-readiness, security, and scalability using Terraform and Google Cloud best practices.

## Overview

The App Factory is an automated system that discovers, vets, develops, and publishes mobile applications. It operates as a collection of containerized microservices and jobs, each acting as a specialized "AI employee" within a digital assembly line. This project leverages Docker, Cloud Run, Cloud Build, API Gateway, Terraform, and other GCP services to create a scalable and autonomous application production pipeline.

## Production-Ready Architecture

* **Infrastructure as Code (IaC)**: All Google Cloud resources, including Cloud Run services, IAM permissions, and secrets, are managed declaratively using **Terraform**. This replaces the previous imperative shell scripts (`deploy.sh`, `iam_setup.sh`).
* **CI/CD Pipeline**: The system is deployed via a CI/CD pipeline orchestrated by **Cloud Build**. The pipeline, defined in `cloudbuild.yaml`, now uses Terraform to plan and apply infrastructure changes. Production deployments require a manual approval step within the Cloud Build process.
* **Environment Management**: The architecture supports distinct `dev` and `prod` environments, managed through Terraform workspaces and `.tfvars` files. This ensures isolation and safe promotion of changes.
* **Secret Management**: All sensitive credentials (API keys, tokens) are securely managed in **Google Secret Manager**. Secrets are provisioned via Terraform and accessed by services at runtime. The insecure `key.properties` file has been removed.
* **State Management**: **Terraform Cloud Storage Backend** is used for securely storing and locking the Terraform state, enabling team collaboration and preventing state corruption.

## How to Deploy

1.  **Prerequisites**:
    * A Google Cloud project.
    * A globally unique Cloud Storage bucket for Terraform state.
    * Required APIs enabled (`gcloud services enable...`).
    * Secrets created in Google Secret Manager (e.g., `github-token`, `gemini-api-key`).

2.  **Configure CI/CD Trigger**:
    * Connect your Git repository to Cloud Build.
    * Create a build trigger that executes the `cloudbuild.yaml` file.
    * Set the `_ENV_SUFFIX` substitution variable on the trigger (`dev` or `prod`) to target the desired environment.

3.  **Run the Pipeline**:
    * Push a commit to the configured branch to start the build.
    * For production deployments (`_ENV_SUFFIX=prod`), manually approve the "Manual Approval" step in the Cloud Build UI to proceed with `terraform apply`.