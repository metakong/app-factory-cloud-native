import os
import traceback
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore
from google.cloud import run_v2

app = Flask(__name__)
logger = get_logger(__name__)

# --- Configuration from Environment Variables ---
PUBLISHER_JOB_NAME = os.environ.get("PUBLISHER_JOB_NAME")

@app.route("/")
def health_check():
    """Provides a simple health check endpoint."""
    return "OK", 200

@app.route('/publish', methods=['POST'])
def publish_app():
    """
    Receives a completed app and triggers the play-publisher-tool Cloud Run Job.
    """
    idea_id = "" # Initialize for error logging
    try:
        [cite_start]if not PUBLISHER_JOB_NAME: # [cite: 126]
            logger.critical("PUBLISHER_JOB_NAME environment variable is not set. Cannot trigger job.")
            return jsonify({"status": "error", "message": "Publishing service is not configured."}), 500

        data = request.get_json()
        if not data or "idea_id" not in data:
            logger.error("Request body missing 'idea_id'.", extra={"json_fields": data})
            [cite_start]return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400 # [cite: 127]

        idea_id = data["idea_id"]
        logger.info(f"Starting publishing process for app idea: {idea_id}")

        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            logger.error(f"App idea '{idea_id}' not found in Firestore.")
            return jsonify({"status": "error", "message": f"App idea '{idea_id}' not found."}), 404

        [cite_start]logger.info(f"Triggering play-publisher-tool job '{PUBLISHER_JOB_NAME}' for idea: {idea_id}") # [cite: 128]
        run_client = run_v2.JobsClient()
        
        request_body = run_v2.RunJobRequest(
            name=PUBLISHER_JOB_NAME,
            overrides={
                "container_overrides": [
                    {
                        [cite_start]"name": "play-publisher-tool", # [cite: 129]
                        "env": [
                            {"name": "IDEA_ID", "value": idea_id}
                        [cite_start]], # [cite: 130]
                    }
                ]
            },
        )
        operation = run_client.run_job(request=request_body)
        [cite_start]logger.info(f"Successfully triggered job. Operation: {operation.metadata.name}") # [cite: 131]

        save_to_firestore("app_ideas", idea_id, {"status": "PUBLISHING_STARTED"})

        return jsonify({"status": "success", "message": f"Publishing workflow started for '{idea_id}'."})

    except Exception as e:
        logger.exception(f"An error occurred during publishing for '{idea_id}'.")
        save_to_firestore("app_ideas", idea_id, {"status": "PUBLISHING_FAILED", "error": str(e)})
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))