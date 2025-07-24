import os
import uuid
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import save_to_firestore, get_from_firestore, db
from google.cloud import run_v2

app = Flask(__name__)
logger = get_logger(__name__)

# --- Configuration ---
PROJECT_ID = os.environ.get("GCP_PROJECT", "app-factory-v2")
REGION = "us-central1"
WEB_SCRAPER_JOB_NAME = f"projects/{PROJECT_ID}/locations/{REGION}/jobs/web-scraper-tool"

@app.route("/")
def health_check():
    """Provides a simple health check endpoint for monitoring."""
    return "OK", 200

@app.route('/start-discovery', methods=['POST'])
def start_discovery_job():
    """Triggers the web-scraper-tool Cloud Run Job to start the entire pipeline."""
    logger.info("Received request to start discovery cycle job.")
    try:
        run_client = run_v2.JobsClient()
        request_body = run_v2.RunJobRequest(name=WEB_SCRAPER_JOB_NAME)
        operation = run_client.run_job(request=request_body)
        
        logger.info(f"Successfully triggered job '{WEB_SCRAPER_JOB_NAME}'. Operation: {operation.metadata.name}")
        return jsonify({"status": "success", "message": "Discovery cycle job started successfully."}), 200
    except Exception as e:
        logger.exception(f"Failed to trigger 'web-scraper-tool' job. Stacktrace: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": "Failed to start discovery job."}), 500

@app.route('/vetted-ideas', methods=['GET'])
def get_ideas_for_approval():
    """Returns a list of app ideas that have passed automated vetting and are ready for CEO approval."""
    logger.info("Request received for ideas awaiting CEO approval.")
    try:
        ideas_ref = db.collection("app_ideas").where("status", "==", "PENDING_CEO_APPROVAL").stream()
        ideas = [idea.to_dict() for idea in ideas_ref]
        return jsonify({"ideas": ideas}), 200
    except Exception as e:
        logger.exception(f"Failed to fetch ideas for approval. Stacktrace: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": "Failed to retrieve app ideas."}), 500

@app.route('/reject-idea', methods=['POST'])
def reject_idea():
    """
    Handles the CEO's rejection of an app idea.
    It updates the idea's status and logs it to the permanent 'rejected_app_ideas' collection.
    """
    idea_id = "" # Initialize for error logging
    try:
        data = request.get_json()
        if not data or "idea_id" not in data:
            logger.error("Request body missing 'idea_id'.")
            return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400

        idea_id = data["idea_id"]
        logger.info(f"Received CEO rejection for idea: {idea_id}")
        
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            logger.error(f"Could not find idea '{idea_id}' to reject.")
            return jsonify({"status": "error", "message": "Idea not found."}), 404

        rejection_reason = "CEO_REJECTED"
        save_to_firestore("app_ideas", idea_id, {"status": rejection_reason})
        
        rejected_idea_data = {
            "original_idea_id": idea_id,
            "description": app_idea.get("description"),
            "rejection_reason": rejection_reason,
            "rejected_at": datetime.utcnow().isoformat()
        }
        save_to_firestore("rejected_app_ideas", idea_id, rejected_idea_data)
        logger.info(f"Idea '{idea_id}' rejected by CEO and logged.")
        
        return jsonify({"status": "success", "message": f"Idea {idea_id} rejected."}), 200
    except Exception as e:
        logger.exception(f"Failed to reject idea '{idea_id}'. Stacktrace: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": "Failed to reject idea."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))