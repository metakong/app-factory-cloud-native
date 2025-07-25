import os
import traceback
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore
import google.generativeai as genai

app = Flask(__name__)
logger = get_logger(__name__)

# --- Configuration ---
# Service URL is now injected via Terraform into the calling service (CSO Vetting)
genai.configure()

@app.route("/")
def health_check():
    """Provides a simple health check endpoint."""
    return "OK", 200

@app.route('/analyze', methods=['POST'])
def analyze_idea():
    """
    Receives a vetted idea, generates a product spec and SWOT analysis using the Gemini API,
    and updates its status to 'PENDING_CEO_APPROVAL'.
    """
    idea_id = "" # Initialize for error logging
    try:
        data = request.get_json()
        if not data or "idea_id" not in data:
            logger.error("Request body missing 'idea_id'.", extra={"json_fields": data})
            return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400

        idea_id = data["idea_id"]
        logger.info(f"Starting product analysis for app idea: {idea_id}")

        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            logger.error(f"App idea '{idea_id}' not found in Firestore.")
            return jsonify({"status": "error", "message": f"App idea '{idea_id}' not found."}), 404

        # --- CORE LOGIC: Generate Product Spec and SWOT Analysis ---
        logger.info(f"Generating product spec and SWOT for: {app_idea.get('description')}")
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Act as a world-class Chief Product Officer for a consumer mobile app startup. Your primary goal is to design products for the "average, non-technical consumer." Based on the following app idea, which was sourced from public online discussions, generate a detailed product specification document. The document must contain these two main sections: "Product Specification" and "SWOT Analysis".
        Under "Product Specification", include:
        1. **Target User Persona**: Describe the ideal user. Focus on their daily life, motivations, and frustrations.
        2. **Problem Statement**: Clearly articulate the core consumer pain point this app solves.
        3. **Core Feature Set (MVP)**: List the essential features for the first version. Prioritize simplicity.
        4. **Monetization Strategy**: Propose a simple, consumer-friendly model.

        Under "SWOT Analysis", include:
        1. **Strengths**: What internal advantages will this app have? (e.g., unique features, simple UI).
        2. **Weaknesses**: What are the internal disadvantages or challenges? (e.g., reliance on third-party data, potential for user churn).
        3. **Opportunities**: What external factors can the app capitalize on? (e.g., growing market trend, lack of a dominant competitor).
        4. **Threats**: What external factors could harm the project? (e.g., a large company entering the space, changing regulations).

        App Idea: "{app_idea.get('description')}"
        """
        response = model.generate_content(prompt)
        product_spec_and_swot = response.text

        updated_data = {
            "status": "PENDING_CEO_APPROVAL",
            "product_spec_and_swot": product_spec_and_swot,
            "error": None
        }
        save_to_firestore("app_ideas", idea_id, updated_data)
        logger.info(f"Successfully generated spec and SWOT for '{idea_id}'. Status set to PENDING_CEO_APPROVAL.")
        
        return jsonify({"status": "success", "message": f"Analysis complete for '{idea_id}'. Ready for CEO review."})

    except Exception as e:
        logger.exception(f"An error occurred during analysis for '{idea_id}'.")
        save_to_firestore("app_ideas", idea_id, {"status": "ANALYSIS_FAILED", "error": str(e)})
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))