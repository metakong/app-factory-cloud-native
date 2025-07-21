import os
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, get_secret

app = Flask(__name__)
logger = get_logger(__name__)

@app.route('/publish', methods=['POST'])
def publish_app():
    """
    Receives a completed app, triggers the final build and publish workflow.
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
        if not app_idea or "github_repo_url" not in app_idea:
            return jsonify({"status": "error", "message": f"GitHub repo for '{idea_id}' not found."}), 404

        # 1. TODO: Logic to trigger the final app build and publishing workflow.
        # This would likely involve creating a new Cloud Build trigger or calling
        # a workflow that checks out the repo, builds the .aab bundle, and calls
        # the play-publisher-tool.
        logger.info(f"Initiating final build for repo: {app_idea['github_repo_url']}... (Placeholder)")

        # 2. Update the status in Firestore.
        updated_data = {"status": "PUBLISHING_STARTED"}
        save_to_firestore("app_ideas", idea_id, updated_data)

        return jsonify({"status": "success", "message": f"Publishing workflow started for '{idea_id}'."})

    except Exception as e:
        logger.error(f"An error occurred during publishing for '{idea_id}': {e}")
        save_to_firestore("app_ideas", idea_id, {"status": "PUBLISHING_FAILED"})
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))