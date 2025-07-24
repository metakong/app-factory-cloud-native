import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import save_to_firestore, get_from_firestore, db

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
        "status": "VETTING_PASSED", # This test route is now out of sync with the main flow
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
def get_ideas_for_approval(): # Function name updated for clarity
    logger.info("Request received for ideas awaiting CEO approval.")
    try:
        # --- UPDATED LINE ---
        # Query for the new status to ensure SWOT analysis is complete before display
        ideas_ref = db.collection("app_ideas").where("status", "==", "PENDING_CEO_APPROVAL").stream()
        ideas = [idea.to_dict() for idea in ideas_ref]
        return jsonify({"ideas": ideas}), 200
    except Exception as e:
        logger.error(f"Failed to fetch ideas for approval from Firestore: {e}")
        return jsonify({"status": "error", "message": "Failed to retrieve app ideas."}), 500

@app.route('/reject-idea', methods=['POST'])
def reject_idea():
    data = request.get_json()
    idea_id = data.get("idea_id")
    logger.info(f"Received CEO rejection for idea: {idea_id}")
    try:
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
        logger.error(f"Failed to reject idea '{idea_id}': {e}")
        return jsonify({"status": "error", "message": "Failed to reject idea."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))