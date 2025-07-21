import os
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore
from google.cloud import run_v2

app = Flask(__name__)
logger = get_logger(__name__)

PROJECT_ID = os.environ.get("GCP_PROJECT", "app-factory-v2")
REGION = "us-central1"

@app.route("/")
def health_check():
    """Provides a simple health check endpoint."""
    return "OK", 200

@app.route('/publish', methods=['POST'])
def publish_app():
    """
    Receives a completed app and triggers the play-publisher-tool Cloud Run Job.
    """
    logger.info("CMO Publishing Agent received a request.")
    data = request.get_json()

    if not data or "idea_id" not in data:
        logger.warning("Request missing 'idea_id'.")
        return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400

    idea_id = data["idea_id"]
    logger.info(f"Starting publishing process for app idea: {idea_id}")

    try:
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            return jsonify({"status": "error", "message": f"App idea '{idea_id}' not found."}), 404

        # 1. Trigger the play-publisher-tool Cloud Run Job
        logger.info(f"Triggering play-publisher-tool job for idea: {idea_id}")
        run_client = run_v2.JobsClient()
        job_name = f"projects/{PROJECT_ID}/locations/{REGION}/jobs/play-publisher-tool"
        
        request_body = run_v2.RunJobRequest(
            name=job_name,
            overrides={
                "container_overrides": [
                    {
                        "name": "play-publisher-tool",
                        "env": [{"name": "IDEA_ID", "value": idea_id}],
                    }
                ]
            },
        )
        operation = run_client.run_job(request=request_body)
        logger.info(f"Successfully triggered job. Operation: {operation.metadata.name}")

        # 2. Update the status in Firestore.
        save_to_firestore("app_ideas", idea_id, {"status": "PUBLISHING_STARTED"})

        return jsonify({"status": "success", "message": f"Publishing workflow started for '{idea_id}'."})

    except Exception as e:
        logger.error(f"An error occurred during publishing for '{idea_id}': {e}")
        save_to_firestore("app_ideas", idea_id, {"status": "PUBLISHING_FAILED", "error": str(e)})
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))