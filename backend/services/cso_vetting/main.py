import os
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore

app = Flask(__name__)
logger = get_logger(__name__)

@app.route('/vet', methods=['POST'])
def vet_idea():
    """
    Receives an app idea ID, retrieves it from Firestore, and performs a mock vetting.
    """
    logger.info("CSO Vetting Service received a request.")
    data = request.get_json()

    if not data or "idea_id" not in data:
        logger.warning("Request missing 'idea_id'.")
        return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400

    idea_id = data["idea_id"]
    logger.info(f"Starting security vetting for app idea: {idea_id}")

    try:
        # 1. Get the idea from Firestore
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            return jsonify({"status": "error", "message": f"App idea '{idea_id}' not found."}), 404

        # 2. Perform mock vetting logic
        logger.info(f"Performing security checks on: {app_idea.get('description')}")
        # ... In a real scenario, complex security checks would happen here ...
        
        # 3. Update the status in Firestore
        updated_data = {"status": "VETTING_PASSED"}
        save_to_firestore("app_ideas", idea_id, updated_data)

        logger.info(f"Security vetting for '{idea_id}' passed.")
        return jsonify({"status": "success", "message": f"Vetting passed for '{idea_id}'."})

    except Exception as e:
        logger.error(f"An error occurred during vetting for '{idea_id}': {e}")
        # Optionally, update Firestore status to "VETTING_FAILED"
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))