# App Factory V2 - Cloud Native (Production Ready)

This repository contains the complete infrastructure-as-code and application source for the App Factory V2 project. This version has been refactored for production-readiness, security, and scalability using Terraform and Google Cloud best practices.

## Production-Ready Architecture

* **Infrastructure as Code (IaC)**: All Google Cloud resources, including Cloud Run services, IAM permissions, Storage Buckets, and API Gateway configs are managed declaratively using **Terraform**. [cite_start]This replaces the previous imperative shell scripts (`deploy.sh`, `iam_setup.sh`). [cite: 5, 60, 61]
* **CI/CD Pipeline**: The system is deployed via a GitOps CI/CD pipeline orchestrated by **Cloud Build**. [cite_start]The pipeline, defined in `cloudbuild.yaml`, now uses Terraform to plan and apply infrastructure changes. [cite: 60] [cite_start]Production deployments require a manual approval step within the Cloud Build process for security and oversight. [cite: 66, 249]
* [cite_start]**Environment Management**: The architecture supports distinct `dev` and `prod` environments, managed through Terraform workspaces and `.tfvars` files. [cite: 250, 74, 79] This ensures isolation and safe promotion of changes.
* **Secure by Default**:
    * [cite_start]**Networking**: All backend microservices are configured with internal-only ingress, removing them from the public internet. [cite: 32, 37, 38] The API Gateway serves as the single, controlled entry point.
    * [cite_start]**Human Access**: The CEO Dashboard is secured with Identity-Aware Proxy (IAP), enforcing zero-trust access for authorized users. [cite: 33, 44]
    * [cite_start]**Data Access**: Public access is disabled on all Cloud Storage buckets. [cite: 13] [cite_start]Temporary access to generated APKs is provided via secure, short-lived V4 Signed URLs. [cite: 104, 105]
* **Secret Management**: All sensitive credentials (API keys, tokens) are securely managed in **Google Secret Manager**. [cite_start]Secrets are provisioned via Terraform and accessed by services at runtime. [cite: 251, 252]
* [cite_start]**State Management**: A dedicated, non-public Cloud Storage bucket is used for the **Terraform Backend** to securely store and lock the Terraform state, enabling team collaboration and preventing state corruption. [cite: 14, 253]

## How to Deploy

1.  **Prerequisites**:
    * A Google Cloud project with the necessary APIs enabled (Cloud Run, IAM, Secret Manager, Cloud Build, etc.).
    * A globally unique Cloud Storage bucket for Terraform state (this will be created by the initial Terraform apply).
    * [cite_start]Secrets created in Google Secret Manager (e.g., `github-token`, `gemini-api-key`). [cite: 256]
2.  **Configure CI/CD Trigger**:
    * [cite_start]Connect your Git repository to Cloud Build. [cite: 257]
    * [cite_start]Create a build trigger that executes the `cloudbuild.yaml` file. [cite: 258]
    * [cite_start]Set the `_ENV_SUFFIX` substitution variable on the trigger (`dev` or `prod`) to target the desired environment. [cite: 259]
3.  **Run the Pipeline**:
    * [cite_start]Push a commit to the configured branch to start the build. [cite: 260]
    * [cite_start]For production deployments (`_ENV_SUFFIX=prod`), manually approve the "Manual Approval" step in the Cloud Build UI to proceed with `terraform apply`. [cite: 261]