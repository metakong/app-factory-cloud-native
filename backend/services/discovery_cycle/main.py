import os
import uuid
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import save_to_firestore, make_internal_request

app = Flask(__name__)
logger = get_logger(__name__)

# The URL for the CSO Vetting Service will be automatically provided by Cloud Run
CSO_VETTING_SERVICE_URL = os.environ.get("CSO_VETTING_SERVICE_URL")

@app.route('/start', methods=['POST'])
def start_cycle():
    """
    Starts a new app discovery cycle.
    1. Creates a new "app_idea" document in Firestore.
    2. Triggers the CSO Vetting Service to begin its process.
    """
    logger.info("Discovery Cycle Service received a request to start.")

    # 1. Generate a new App Idea and save it to Firestore
    idea_id = f"idea-{uuid.uuid4()}"
    app_idea_data = {
        "idea_id": idea_id,
        "status": "PENDING_VETTING",
        "description": "A revolutionary new mobile app for discovering local coffee shops."
        # In a real scenario, this data would come from the web-scraper-tool
    }

    try:
        save_to_firestore("app_ideas", idea_id, app_idea_data)
    except Exception as e:
        logger.error(f"Failed to save new app idea '{idea_id}' to Firestore: {e}")
        return jsonify({"status": "error", "message": "Could not save app idea."}), 500

    # 2. Trigger the CSO Vetting Service
    if not CSO_VETTING_SERVICE_URL:
        logger.error("CSO_VETTING_SERVICE_URL environment variable is not set.")
        return jsonify({"status": "error", "message": "Downstream service is not configured."}), 500

    logger.info(f"Triggering CSO Vetting Service for idea '{idea_id}' at {CSO_VETTING_SERVICE_URL}")

    try:
        vetting_request_data = {"idea_id": idea_id}
        # This is a secure, authenticated call from one Cloud Run service to another
        response = make_internal_request(
            service_url=f"{CSO_VETTING_SERVICE_URL}/vet", 
            method='POST', 
            data=vetting_request_data
        )
        logger.info(f"CSO Vetting Service responded with status {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Failed to trigger CSO Vetting Service for idea '{idea_id}': {e}")
        # Here you might add logic to update the Firestore status to "VETTING_FAILED"
        return jsonify({"status": "error", "message": "Failed to trigger downstream service."}), 500

    return jsonify({
        "status": "success",
        "message": f"Discovery cycle started. App idea '{idea_id}' is now pending security vetting."
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))