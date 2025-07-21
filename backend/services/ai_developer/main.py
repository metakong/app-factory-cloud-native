import os
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, make_internal_request, get_secret, db

app = Flask(__name__)
logger = get_logger(__name__)

@app.route("/")
def health_check():
    return "OK", 200

@app.route('/develop', methods=['POST'])
def develop_app():
    data = request.get_json()
    idea_id = data.get("idea_id")
    feedback = data.get("feedback")
    logger.info(f"Development request for idea: {idea_id} with feedback: '{feedback}'")
    try:
        # TODO: Add logic to use feedback in prompts
        save_to_firestore("app_ideas", idea_id, {
            "status": "PENDING_CEO_REVISION",
            "ceo_feedback": feedback,
            # Placeholder for the APK download URL
            "apk_download_url": "https://storage.googleapis.com/app-factory-apks/placeholder.apk"
        })
        return jsonify({"status": "success", "message": f"Development started for {idea_id}."}), 200
    except Exception as e:
        logger.error(f"Development failed for '{idea_id}': {e}")
        return jsonify({"status": "error", "message": "Development failed."}), 500

@app.route('/developed-apks', methods=['GET'])
def get_developed_apks():
    logger.info("Request received for developed APKs.")
    try:
        apks_ref = db.collection("app_ideas").where("status", "==", "PENDING_CEO_REVISION").stream()
        apks = [apk.to_dict() for apk in apks_ref]
        return jsonify({"apks": apks}), 200
    except Exception as e:
        logger.error(f"Failed to fetch developed APKs: {e}")
        return jsonify({"status": "error", "message": "Failed to retrieve APKs."}), 500

@app.route('/revise', methods=['POST'])
def revise_app():
    # Placeholder for revision logic
    data = request.get_json()
    idea_id = data.get("idea_id")
    feedback = data.get("feedback")
    logger.info(f"Revision request for idea: {idea_id} with feedback: '{feedback}'")
    save_to_firestore("app_ideas", idea_id, {"status": "PENDING_CEO_REVISION", "ceo_revision_feedback": feedback})
    return jsonify({"status": "success", "message": f"Revision in progress for {idea_id}."}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))