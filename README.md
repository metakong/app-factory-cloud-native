# App Factory V2 - Cloud Native

This repository contains the complete infrastructure-as-code and application source for the App Factory V2 project, a pragmatic and functional prototype designed to run entirely on the Google Cloud Platform.

## Overview

The App Factory is an automated system that discovers, vets, develops, and publishes mobile applications. It operates as a collection of containerized microservices and jobs, each acting as a specialized "AI employee" within a digital assembly line. This project leverages Docker, Cloud Run, Cloud Build, API Gateway, and other GCP services to create a scalable and autonomous application production pipeline.

## Current Architecture

The current architecture is a functional, end-to-end prototype designed for rapid iteration and deployment.

* **Frontend**: A static HTML/CSS/JavaScript single-page application that serves as the **CEO Dashboard**. [cite_start]It is deployed as a dedicated, publicly accessible Cloud Run service. [cite: 1981, 1982]
* **API Layer**: A **Google Cloud API Gateway** provides a single, secure endpoint for the frontend. [cite_start]It uses an API key for authentication and routes requests to the appropriate backend services as defined in `api-spec.yaml`. [cite: 2, 3, 4, 5, 6]
* **Backend Services**: The backend consists of multiple Python-based microservices, each running in its own container on **Cloud Run**. [cite_start]Services are configured with specific ingress settings (e.g., `internal-and-cloud-load-balancing`) and dedicated IAM service accounts for security. [cite: 1946, 1947, 1962, 1965, 1971, 1973, 1977]
* [cite_start]**Backend Jobs**: Long-running or intensive tasks, such as the `web-scraper-tool` and `play-publisher-tool`, are implemented as **Cloud Run Jobs** to run to completion without tying up service resources. [cite: 1947, 1950]
* **CI/CD Pipeline**: The entire system is deployed via a CI/CD pipeline orchestrated by **Cloud Build** and defined in `cloudbuild.yaml`. The pipeline is triggered on a `git push` to the `main` branch. [cite_start]It uses `docker compose` to build and push all service images to Artifact Registry, followed by a custom `deploy.sh` script that handles the deployment of each service to Cloud Run. [cite: 6, 7]
* [cite_start]**State Management**: **Firestore** is used as the central database to track the state of each app idea as it moves through the production pipeline (e.g., `PENDING_VETTING`, `PENDING_CEO_APPROVAL`). [cite: 1956, 1963, 1964]
* **Security**: All sensitive credentials (API keys, tokens) are managed securely in **Google Secret Manager** and are injected into the appropriate Cloud Run services at runtime. [cite_start]The `.env` file is explicitly ignored via `.gitignore` and is not used for cloud deployments. [cite: 1, 1947]

## Core Services & Tools

* `ceo-dashboard`: The frontend user interface for the CEO.
* `discovery-cycle-service`: The primary backend service that manages the lifecycle of app ideas.
* `cso-vetting-service`: An AI agent that analyzes the market competition for a new idea.
* `cpo-analysis-service`: An AI agent that generates a detailed product specification and SWOT analysis.
* `ai-developer-agent-service`: The core development agent responsible for generating code and managing the build process.
* `cmo-publishing-agent`: An agent that orchestrates the final publishing of the app to the Google Play Store.
* `web-scraper-tool`: A Cloud Run Job that scrapes public forums to source new app ideas.
* `play-publisher-tool`: A Cloud Run Job that handles the technical steps of uploading and publishing the final app bundle.