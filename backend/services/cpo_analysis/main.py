import os
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, make_internal_request
import google.generativeai as genai

app = Flask(__name__)
logger = get_logger(__name__)

# The URLs for downstream services are provided by Cloud Run
AI_DEVELOPER_AGENT_SERVICE_URL = os.environ.get("AI_DEVELOPER_AGENT_SERVICE_URL")

# Configure the Gemini API client (will use Application Default Credentials)
genai.configure()

@app.route("/")
def health_check():
    """Provides a simple health check endpoint."""
    return "OK", 200

@app.route('/analyze', methods=['POST'])
def analyze_idea():
    """
    Receives a vetted app idea, calls the Gemini API to generate a
    product specification, and triggers the AI Developer service.
    """
    logger.info("CPO Analysis Service received a request.")
    data = request.get_json()

    if not data or "idea_id" not in data:
        logger.warning("Request missing 'idea_id'.")
        return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400

    idea_id = data["idea_id"]
    logger.info(f"Starting product analysis for app idea: {idea_id}")

    try:
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            return jsonify({"status": "error", "message": f"App idea '{idea_id}' not found."}), 404

        # 1. Call Gemini API to generate a detailed product specification.
        logger.info(f"Generating product spec for: {app_idea.get('description')}")
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"""
        Act as a world-class Chief Product Officer. Based on the following high-level app idea,
        generate a detailed product specification document.
        The spec should include:
        1. A target user persona.
        2. A list of core features (MVP).
        3. A proposed technology stack (Flutter with Riverpod for state management).
        4. A monetization strategy.

        App Idea: "{app_idea.get('description')}"
        """
        response = model.generate_content(prompt)
        product_spec = response.text

        # 2. Save the new spec to Firestore and update status.
        updated_data = {
            "status": "ANALYSIS_PASSED",
            "product_spec": product_spec
        }
        save_to_firestore("app_ideas", idea_id, updated_data)
        logger.info(f"Successfully generated and saved product spec for '{idea_id}'.")

        # 3. Trigger the AI Developer Agent service.
        if not AI_DEVELOPER_AGENT_SERVICE_URL:
            logger.error("AI_DEVELOPER_AGENT_SERVICE_URL environment variable is not set.")
            save_to_firestore("app_ideas", idea_id, {"status": "DEV_TRIGGER_FAILED"})
            return jsonify({"status": "error", "message": "Downstream AI Developer service is not configured."}), 500

        logger.info(f"Triggering AI Developer service for idea '{idea_id}' at {AI_DEVELOPER_AGENT_SERVICE_URL}")
        dev_request_data = {"idea_id": idea_id}
        dev_response = make_internal_request(
            service_url=f"{AI_DEVELOPER_AGENT_SERVICE_URL}/develop",
            method='POST',
            data=dev_request_data
        )
        logger.info(f"AI Developer service responded with status {dev_response.status_code}: {dev_response.text}")

        return jsonify({"status": "success", "message": f"Analysis complete for '{idea_id}' and development triggered."})

    except Exception as e:
        logger.error(f"An error occurred during analysis for '{idea_id}': {e}")
        save_to_firestore("app_ideas", idea_id, {"status": "ANALYSIS_FAILED"})
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))