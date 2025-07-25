import os
import traceback
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import db
from google.cloud import run_v2

app = Flask(__name__)
logger = get_logger(__name__)

# --- Configuration from Environment Variables ---
WEB_SCRAPER_JOB_NAME = os.environ.get("WEB_SCRAPER_JOB_NAME")

@app.route("/")
def health_check():
    """Provides a simple health check endpoint."""
    return "OK", 200

@app.route('/start-discovery', methods=['POST'])
def start_discovery_job():
    """Triggers the web-scraper-tool Cloud Run Job."""
    logger.info("Received request to start discovery cycle job.")
    try:
        if not WEB_SCRAPER_JOB_NAME:
            logger.critical("WEB_SCRAPER_JOB_NAME environment variable is not set. Cannot trigger job.")
            return jsonify({"status": "error", "message": "Discovery service is not configured."}), 500

        run_client = run_v2.JobsClient()
        request_body = run_v2.RunJobRequest(name=WEB_SCRAPER_JOB_NAME)
        operation = run_client.run_job(request=request_body)
        
        logger.info(f"Successfully triggered job '{WEB_SCRAPER_JOB_NAME}'. Operation: {operation.metadata.name}")
        return jsonify({"status": "success", "message": "Discovery cycle job started successfully."}), 200
    except Exception as e:
        logger.exception("Failed to trigger 'web-scraper-tool' job.")
        return jsonify({"status": "error", "message": "Failed to start discovery job."}), 500

@app.route('/vetted-ideas', methods=['GET'])
def get_ideas_for_approval():
    """Returns a list of app ideas ready for CEO approval."""
    logger.info("Request received for ideas awaiting CEO approval.")
    try:
        ideas_ref = db.collection("app_ideas").where("status", "==", "PENDING_CEO_APPROVAL").stream()
        ideas = [idea.to_dict() for idea in ideas_ref]
        return jsonify({"ideas": ideas}), 200
    except Exception as e:
        logger.exception("Failed to fetch ideas for approval.")
        return jsonify({"status": "error", "message": "Failed to retrieve app ideas."}), 500