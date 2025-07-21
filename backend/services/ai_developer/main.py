import os
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, make_internal_request, get_secret

app = Flask(__name__)
logger = get_logger(__name__)

# URLs for other services
CMO_PUBLISHING_AGENT_URL = os.environ.get("CMO_PUBLISHING_AGENT_URL")
MCP_GATEWAY_URL = os.environ.get("MCP_GATEWAY_URL")


@app.route('/develop', methods=['POST'])
def develop_app():
    """
    Receives a product specification, generates source code, commits it to a new
    GitHub repository, and triggers the CMO Publishing agent.
    """
    logger.info("AI Developer Agent received a request.")
    data = request.get_json()

    if not data or "idea_id" not in data:
        logger.warning("Request missing 'idea_id'.")
        return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400

    idea_id = data["idea_id"]
    logger.info(f"Starting development for app idea: {idea_id}")

    try:
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea or "product_spec" not in app_idea:
            return jsonify({"status": "error", "message": f"Product spec for '{idea_id}' not found."}), 404

        # 1. TODO: Call Gemini API with the product spec to generate Flutter source code.
        # This is a highly complex task that will involve multiple prompts and parsing.
        # For now, we will create a placeholder file.
        logger.info("Generating source code... (Placeholder)")
        generated_code = "print('Hello, World!')"
        repo_name = f"app-{idea_id}"

        # 2. Call the github-tool via MCP Gateway to create a repo.
        if not MCP_GATEWAY_URL:
            logger.error("MCP_GATEWAY_URL environment variable is not set.")
            save_to_firestore("app_ideas", idea_id, {"status": "DEVELOPMENT_FAILED"})
            return jsonify({"status": "error", "message": "MCP Gateway is not configured."}), 500

        logger.info(f"Creating GitHub repo '{repo_name}' via MCP Gateway.")
        github_repo_url = None
        try:
            # The github-tool likely exposes a REST-like interface through the gateway.
            # We'll assume a POST to /github-tool/repos creates a new repository.
            # The owner is inferred from the GITHUB_TOKEN used by the tool.
            repo_creation_data = {"name": repo_name, "description": app_idea.get('description')}
            repo_response = make_internal_request(
                service_url=f"{MCP_GATEWAY_URL}/github-tool/repos",
                method='POST',
                data=repo_creation_data
            )
            github_repo_url = repo_response.json().get("html_url")
            if not github_repo_url:
                raise ValueError("Response from repo creation did not contain 'html_url'.")
            logger.info(f"Successfully created GitHub repo: {github_repo_url}")
        except Exception as e:
            logger.error(f"Failed to create GitHub repo for idea '{idea_id}': {e}")
            save_to_firestore("app_ideas", idea_id, {"status": "REPO_CREATION_FAILED"})
            return jsonify({"status": "error", "message": "Failed to create GitHub repository."}), 500

        # 3. Save the new repo URL and update status in Firestore.
        updated_data = {"status": "CODE_GENERATED", "github_repo_url": github_repo_url}
        save_to_firestore("app_ideas", idea_id, updated_data)

        # 4. Trigger the CMO Publishing Agent.
        if not CMO_PUBLISHING_AGENT_URL:
            logger.error("CMO_PUBLISHING_AGENT_URL environment variable is not set.")
            save_to_firestore("app_ideas", idea_id, {"status": "PUBLISH_TRIGGER_FAILED"})
            return jsonify({"status": "error", "message": "Downstream CMO agent is not configured."}), 500

        logger.info(f"Triggering CMO Publishing agent for idea '{idea_id}' at {CMO_PUBLISHING_AGENT_URL}")
        publish_request_data = {"idea_id": idea_id}
        publish_response = make_internal_request(
            service_url=f"{CMO_PUBLISHING_AGENT_URL}/publish",
            method='POST',
            data=publish_request_data
        )
        logger.info(f"CMO Publishing agent responded with status {publish_response.status_code}: {publish_response.text}")

        return jsonify({"status": "success", "message": f"Development complete for '{idea_id}' and publishing triggered."})

    except Exception as e:
        logger.error(f"An error occurred during development for '{idea_id}': {e}")
        save_to_firestore("app_ideas", idea_id, {"status": "DEVELOPMENT_FAILED"})
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))