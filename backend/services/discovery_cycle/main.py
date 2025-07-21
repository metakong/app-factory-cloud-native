import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import save_to_firestore, db

app = Flask(__name__)
logger = get_logger(__name__)

@app.route("/")
def health_check():
    return "OK", 200

@app.route('/start', methods=['POST'])
def start_cycle():
    logger.info("Discovery Cycle Service received a request to start.")
    idea_id = f"idea-{uuid.uuid4()}"
    app_idea_data = {
        "idea_id": idea_id,
        "status": "VETTING_PASSED", # Simulating passing for dashboard test
        "description": "A new mobile app that helps users find and trade rare houseplants.",
        "created_at": datetime.utcnow().isoformat()
    }
    try:
        save_to_firestore("app_ideas", idea_id, app_idea_data)
    except Exception as e:
        logger.error(f"Failed to save new app idea '{idea_id}': {e}")
        return jsonify({"status": "error", "message": "Could not save app idea."}), 500
    return jsonify({"status": "success", "message": f"Discovery cycle started for idea '{idea_id}'."})

@app.route('/vetted-ideas', methods=['GET'])
def get_vetted_ideas():
    logger.info("Request received for vetted ideas.")
    try:
        ideas_ref = db.collection("app_ideas").where("status", "==", "VETTING_PASSED").stream()
        ideas = [idea.to_dict() for idea in ideas_ref]
        return jsonify({"ideas": ideas}), 200
    except Exception as e:
        logger.error(f"Failed to fetch vetted ideas from Firestore: {e}")
        return jsonify({"status": "error", "message": "Failed to retrieve app ideas."}), 500

@app.route('/reject-idea', methods=['POST'])
def reject_idea():
    data = request.get_json()
    idea_id = data.get("idea_id")
    logger.info(f"Received rejection for idea: {idea_id}")
    try:
        save_to_firestore("app_ideas", idea_id, {"status": "CEO_REJECTED"})
        return jsonify({"status": "success", "message": f"Idea {idea_id} rejected."}), 200
    except Exception as e:
        logger.error(f"Failed to reject idea '{idea_id}': {e}")
        return jsonify({"status": "error", "message": "Failed to reject idea."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))