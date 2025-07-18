# App Factory V2 - Cloud Native

This repository contains the complete infrastructure-as-code and application source for the App Factory V2 project, designed to run entirely on the Google Cloud Platform.

## Overview

The App Factory is an automated system that discovers, vets, develops, and publishes mobile applications. It operates as a collection of containerized microservices, each acting as a specialized "AI employee" within a digital assembly line. This project leverages Docker, Cloud Run, Cloud Build, and other GCP services to create a scalable and autonomous application production pipeline.

### Architecture

- **CI/CD:** Managed by Cloud Build, triggered by pushes to the `main` branch.
- **Orchestration:** Cloud Run services are defined and deployed via a `compose.yaml` file.
- **Services:** Each service (`discovery-cycle`, `cso-vetting`, etc.) runs as an independent Cloud Run service with a dedicated IAM service account.
- **Tools:** Long-running or heavy tasks (`robust-web-scraper`, `google-play-publisher`) are designed to run as Cloud Run Jobs.
- **Security:** Secrets are managed via Google Secret Manager. Service-to-service communication will be secured through IAM and service account identities.