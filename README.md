> **Transparency Notice:** This documentation was authored by Claude Sonnet 4.6 (Anthropic) under direct human oversight — the same iterative, human-in-the-loop AI partnership methodology used to architect and build every system in this portfolio.

> **Portfolio Context** | **Sean Deardorff** — Strategic Operations & Business Development
>
> This repository is an artifact of high-velocity, AI-partnered process engineering. It demonstrates how the author builds resilient, automated business machinery — translating the same decoupled logic, governance, and defensive optimization used to manage open sales territories and corporate operations into working code.
>
> **Career Connection:** This production-grade IaC deployment mirrors the same consultancy pattern Sean executed across eight independent client portfolios at MetaKong LLC — assess a messy infrastructure, design a clean architecture with proper governance, deploy it, and measure the revenue impact. The tooling shifted from Salesforce and Zoho to Terraform and Cloud Build, but the methodology of translating chaos into repeatable, documented systems is identical.
>
> [View Full Portfolio →](https://github.com/metakong/sean-deardorff)

---

# App Factory V2 - Cloud Native (Production Ready)

This repository contains the complete infrastructure-as-code and application source for the App Factory V2 project. [cite_start]This version has been refactored for production-readiness, security, and scalability using Terraform and Google Cloud best practices. [cite: 2257]

## Production-Ready Architecture

* [cite_start]**Infrastructure as Code (IaC)**: All Google Cloud resources, including Cloud Run services, IAM permissions, Storage Buckets, and API Gateway configs are managed declaratively using **Terraform**. 
* [cite_start]**CI/CD Pipeline**: The system is deployed via a GitOps CI/CD pipeline orchestrated by **Cloud Build**. [cite: 2260]
* [cite_start]**Environment Management**: The architecture supports distinct `dev` and `prod` environments, managed through Terraform workspaces and `.tfvars` files. [cite: 2263]
* **Secure by Default**:
    * [cite_start]**Networking**: All backend microservices are configured with internal-only ingress. [cite: 2265] The API Gateway serves as the single, controlled entry point.
    * [cite_start]**Human Access**: The CEO Dashboard is secured with Identity-Aware Proxy (IAP). [cite: 2267]
    * [cite_start]**Data Access**: Public access is disabled on all Cloud Storage buckets. [cite: 2268]
* [cite_start]**Secret Management**: All sensitive credentials are securely managed in **Google Secret Manager**. [cite: 2270]
* [cite_start]**State Management**: A dedicated, non-public Cloud Storage bucket is used for the **Terraform Backend**. [cite: 2272]

## How to Deploy

1.  **Prerequisites**:
    * [cite_start]A Google Cloud project with the necessary APIs enabled. 
    * [cite_start]Secrets created in Google Secret Manager. 
2.  **Configure CI/CD Trigger**:
    * [cite_start]Connect your Git repository to Cloud Build. 
    * [cite_start]Create a build trigger that executes `cloudbuild.yaml`. 
    * [cite_start]Set the `_ENV_SUFFIX` substitution variable (`dev` or `prod`). 
3.  **Run the Pipeline**:
    * [cite_start]Push a commit to the configured branch. 
    * [cite_start]For production deployments, manually approve the deployment in the Cloud Build UI.