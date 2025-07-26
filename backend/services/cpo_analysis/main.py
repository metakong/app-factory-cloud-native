import os
import traceback
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, get_secret
import google.generativeai as genai

app = Flask(__name__)
logger = get_logger(__name__)

# --- Configuration ---
# Configure the Gemini client at startup
try:
    gemini_api_key = get_secret("gemini-api-key")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
    else:
        logger.critical("GEMINI_API_KEY secret not found. CPO analysis will fail.")
except Exception as e:
    logger.critical(f"Failed to configure Gemini client: {e}")


@app.route("/")
def health_check():
    [cite_start]"""Provides a simple health check endpoint.""" # [cite: 95]
    return "OK", 200


@app.route('/analyze', methods=['POST'])
def analyze_idea():
    """
    Receives a vetted idea, generates a product spec and SWOT analysis using the Gemini API,
    and updates its status to 'PENDING_CEO_APPROVAL'.
    [cite_start]""" # [cite: 96]
    idea_id = ""  # Initialize for error logging
    try:
        data = request.get_json()
        if not data or "idea_id" not in data:
            logger.error("Request body missing 'idea_id'.", extra={"json_fields": data})
            return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400

        idea_id = data["idea_id"]
        [cite_start]logger.info(f"Starting product analysis for app idea: {idea_id}") # [cite: 97]

        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            logger.error(f"App idea '{idea_id}' not found in Firestore.")
            return jsonify({"status": "error", "message": f"App idea '{idea_id}' not found."}), 404

        # --- CORE LOGIC: Generate Product Spec and SWOT Analysis ---
        logger.info(f"Generating product spec and SWOT for: {app_idea.get('description')}")
        
        [cite_start]model = genai.GenerativeModel('gemini-pro') # [cite: 98]
        prompt = f"""
        Act as a world-class Chief Product Officer for a consumer mobile app startup.
        [cite_start]Your primary goal is to design products for the "average, non-technical consumer." [cite: 99]
        [cite_start]Based on the following app idea, which was sourced from public online discussions, generate a detailed product specification document. [cite: 100]
        [cite_start]The document must contain these two main sections: "Product Specification" and "SWOT Analysis". [cite: 101]
        Under "Product Specification", include:
        1. **Target User Persona**: Describe the ideal user. [cite_start]Focus on their daily life, motivations, and frustrations. [cite: 102, 103]
        2. [cite_start]**Problem Statement**: Clearly articulate the core consumer pain point this app solves. [cite: 104]
        3. **Core Feature Set (MVP)**: List the essential features for the first version. [cite_start]Prioritize simplicity. [cite: 105]
        4. **Monetization Strategy**: Propose a simple, consumer-friendly model.

        Under "SWOT Analysis", include:
        1. **Strengths**: What internal advantages will this app have? [cite_start](e.g., unique features, simple UI). [cite: 106]
        2. **Weaknesses**: What are the internal disadvantages or challenges? [cite_start](e.g., reliance on third-party data, potential for user churn). [cite: 107]
        3. **Opportunities**: What external factors can the app capitalize on? [cite_start](e.g., growing market trend, lack of a dominant competitor). [cite: 108]
        4. **Threats**: What external factors could harm the project? [cite_start](e.g., a large company entering the space, changing regulations). [cite: 109]

        App Idea: "{app_idea.get('description')}"
        """
        response = model.generate_content(prompt)
        product_spec_and_swot = response.text

        updated_data = {
            "status": "PENDING_CEO_APPROVAL",
            "product_spec_and_swot": product_spec_and_swot,
            "error": None
        }
        [cite_start]save_to_firestore("app_ideas", idea_id, updated_data) # [cite: 110]

        logger.info(f"Successfully generated spec and SWOT for '{idea_id}'. Status set to PENDING_CEO_APPROVAL.")
        return jsonify({"status": "success", "message": f"Analysis complete for '{idea_id}'. Ready for CEO review."})

    except Exception as e:
        logger.exception(f"An error occurred during analysis for '{idea_id}'.")
        # Save error state to Firestore for visibility
        if idea_id:
            [cite_start]save_to_firestore("app_ideas", idea_id, {"status": "ANALYSIS_FAILED", "error": str(e)}) # [cite: 111]
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))