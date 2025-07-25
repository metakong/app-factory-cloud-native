import os
import json
import traceback
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, get_secret
import google.generativeai as genai
from github import Github, GithubException, InputGitTreeElement
from google.cloud import storage
from google.cloud.devtools import cloudbuild_v1
from datetime import timedelta

app = Flask(__name__)
logger = get_logger(__name__)

# [cite_start]--- Constants & Configuration from Environment Variables [cite: 110] ---
METAKONG_GITHUB_USER = "metakong"
GITHUB_SECRET_NAME = "github-token"
GEMINI_SECRET_NAME = "gemini-api-key"
PROJECT_ID = os.environ.get("GCP_PROJECT")
APK_BUCKET_NAME = os.environ.get("APK_BUCKET_NAME")

# --- GCP Client Initialization ---
try:
    build_client = cloudbuild_v1.CloudBuildClient()
    storage_client = storage.Client()
except Exception as e:
    logger.critical(f"Failed to initialize GCP clients: {e}")

#... (imports and app setup remain the same)

# --- Secure Internal CI/CD Template ---
# The public access step has been removed.
GENERATED_APP_CLOUDBUILD_TEMPLATE = """
steps:
# 1. Access Keystore from Secret Manager
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      gcloud secrets versions access latest --secret="flutter-keystore-jks" --project="${PROJECT_ID}" --format='get(payload.data)' | tr '_-' '/+' | base64 -d > android/app/keystore.jks
# 2. Access Key Properties from Secret Manager
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      gcloud secrets versions access latest --secret="flutter-key-properties" --project="${PROJECT_ID}" --out-file="android/key.properties"
# 3. Setup Flutter and Build APK
- name: 'cirrusci/flutter:stable'
  args: ['flutter', 'build', 'apk', '--release']
# 4. Upload APK to Cloud Storage
- name: 'gcr.io/cloud-builders/gsutil'
  args:
    - 'cp'
    - 'build/app/outputs/flutter-apk/app-release.apk'
    - 'gs://{apk_bucket_name}/{idea_id}/app-release.apk'
# 5. Notify App Factory of Build Completion
- name: 'gcr.io/cloud-builders/curl'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      set -e
      ACCESS_TOKEN=$(gcloud auth print-identity-token --audiences="{developer_service_url}")
      curl -X POST "{developer_service_url}/build-complete" -H "Authorization: Bearer \\$$ACCESS_TOKEN" -H "Content-Type: application/json" -d '{ "idea_id": "{idea_id}", "build_status": "$$BUILD_STATUS" }'
options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'
"""

#... (rest of the file remains the same)
# (The rest of ai_developer/main.py remains largely the same, but with all `print` calls
# replaced by `logger` calls and the following change in the `build_complete` function)

@app.route('/build-complete', methods=['POST'])
def build_complete():
    """Callback endpoint for the generated app's Cloud Build pipeline."""
    data = request.get_json()
    idea_id = data.get("idea_id")
    build_status = data.get("build_status")

    if not all([idea_id, build_status]):
        logger.error("Invalid build-complete callback payload.", extra={"json_fields": data})
        return jsonify({"status": "error", "message": "Invalid payload. 'idea_id' and 'build_status' are required."}), 400

    logger.info(f"Received build completion for idea '{idea_id}' with status '{build_status}'.")

    try:
        if build_status == "SUCCESS":
            # [cite_start]Generate a secure, time-limited signed URL instead of a public link [cite: 104, 105]
            bucket = storage_client.bucket(APK_BUCKET_NAME)
            blob = bucket.blob(f"{idea_id}/app-release.apk")

            signed_url = blob.generate_v4_signed_url(
                version="v4",
                expiration=timedelta(hours=24), # URL is valid for 24 hours
                method="GET",
            [cite_start]) # [cite: 107]
            
            update_data = {
                "status": "PENDING_CEO_TESTING",
                "apk_download_url": signed_url # Use the secure URL
            }
            message = f"Build for {idea_id} succeeded. APK is ready for testing."
        else:
            update_data = {
                "status": "BUILD_FAILED",
                "error": "The Cloud Build pipeline for the generated application failed."
            }
            message = f"Build for {idea_id} failed."

        save_to_firestore("app_ideas", idea_id, update_data)
        logger.info(message)
        return jsonify({"status": "success", "message": message}), 200

    except Exception as e:
        logger.exception(f"Failed to process build-complete callback for '{idea_id}'.")
        return jsonify({"status": "error", "message": "Failed to update status."}), 500