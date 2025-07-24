import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, make_internal_request
from google_play_scraper import search

app = Flask(__name__)
logger = get_logger(__name__)

CPO_ANALYSIS_SERVICE_URL = os.environ.get("CPO_ANALYSIS_SERVICE_URL")

# --- Competition Analysis Configuration ---
HACKERNEWS_API_URL = "http://hn.algolia.com/api/v1/search?query="
STACKEXCHANGE_API_URL = "https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&site=stackoverflow&q="
REJECTION_THRESHOLD = 7.5

def calculate_competition_score(description: str) -> float:
    """
    Calculates a competition score from 0-10 based on search results.
    10 = no competition, 0 = saturated market.
    """
    logger.info(f"Performing competition analysis for: '{description}'")
    keywords = " ".join(description.split()[:5])

    weights = {"play_store": 0.6, "hacker_news": 0.3, "stack_exchange": 0.1}
    total_weighted_hits = 0

    try:
        # 1. Google Play Store Search
        play_results = search(keywords, n_hits=50)
        play_hits = len(play_results)
        normalized_play_hits = min(play_hits / 50.0, 1.0)
        total_weighted_hits += weights["play_store"] * normalized_play_hits
        logger.info(f"Play Store found {play_hits} potential competitors.")

        # 2. Hacker News Search
        hn_res = requests.get(f"{HACKERNEWS_API_URL}{keywords}", timeout=10)
        hn_res.raise_for_status()
        hn_hits = hn_res.json().get("nbHits", 0)
        normalized_hn_hits = min(hn_hits / 50.0, 1.0)
        total_weighted_hits += weights["hacker_news"] * normalized_hn_hits
        logger.info(f"Hacker News found {hn_hits} related posts.")

        # 3. Stack Exchange Search
        se_res = requests.get(f"{STACKEXCHANGE_API_URL}{keywords}", timeout=10)
        se_res.raise_for_status()
        se_hits = len(se_res.json().get("items", []))
        normalized_se_hits = min(se_hits / 50.0, 1.0)
        total_weighted_hits += weights["stack_exchange"] * normalized_se_hits
        logger.info(f"Stack Exchange found {se_hits} related questions.")

    except requests.RequestException as e:
        logger.warning(f"Could not complete competition analysis search: {e}")
        return 5.0

    final_score = 10 * (1 - total_weighted_hits)
    return round(final_score, 2)

@app.route("/")
def health_check():
    return "OK", 200

@app.route('/vet', methods=['POST'])
def vet_idea():
    logger.info("CSO Vetting Service received a request.")
    data = request.get_json()
    idea_id = data.get("idea_id")

    if not idea_id:
        return jsonify({"status": "error", "message": "Missing 'idea_id' in request body."}), 400

    try:
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            return jsonify({"status": "error", "message": f"App idea '{idea_id}' not found."}), 404
        
        score = calculate_competition_score(app_idea.get("description", ""))
        
        if score < REJECTION_THRESHOLD:
            rejection_reason = "REJECTED_COMPETITION"
            save_to_firestore("app_ideas", idea_id, {"status": rejection_reason, "competition_score": score})
            
            rejected_idea_data = {
                "original_idea_id": idea_id,
                "description": app_idea.get("description"),
                "rejection_reason": rejection_reason,
                "competition_score": score,
                "rejected_at": datetime.utcnow().isoformat()
            }
            save_to_firestore("rejected_app_ideas", idea_id, rejected_idea_data)
            logger.info(f"Idea '{idea_id}' rejected and logged. Score: {score}")
            return jsonify({"status": "success", "message": f"Idea '{idea_id}' rejected due to high competition."}), 200

        # --- UPDATED LINE ---
        # Set status to PENDING_ANALYSIS instead of VETTING_PASSED
        save_to_firestore("app_ideas", idea_id, {"status": "PENDING_ANALYSIS", "competition_score": score})
        logger.info(f"Vetting passed with score {score}. Status set to PENDING_ANALYSIS.")

        if not CPO_ANALYSIS_SERVICE_URL:
            logger.error("CPO_ANALYSIS_SERVICE_URL is not set.")
            save_to_firestore("app_ideas", idea_id, {"status": "ANALYSIS_TRIGGER_FAILED"})
            return jsonify({"status": "error", "message": "Downstream service (CPO) is not configured."}), 500

        make_internal_request(
            service_url=f"{CPO_ANALYSIS_SERVICE_URL}/analyze",
            method='POST',
            data={"idea_id": idea_id}
        )
        return jsonify({"status": "success", "message": f"Vetting passed for '{idea_id}' and analysis triggered."})

    except Exception as e:
        logger.error(f"An error occurred during vetting for '{idea_id}': {e}")
        save_to_firestore("app_ideas", idea_id, {"status": "VETTING_FAILED", "error": str(e)})
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))