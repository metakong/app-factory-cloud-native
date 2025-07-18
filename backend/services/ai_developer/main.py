import os
from flask import Flask, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_secret

app = Flask(__name__)
logger = get_logger(__name__)

@app.route('/')
def handle_request():
    logger.info("AI Developer Agent Service received a request.")
    # Example of using a secret
    api_key = get_secret("gemini-api-key")
    if not api_key:
        logger.error("Could not retrieve Gemini API key.")
        return jsonify({"status": "error", "message": "Missing secret"}), 500

    # Placeholder for development logic
    logger.info("Development logic would run here.")
    return jsonify({"status": "success", "message": "AI Developer task placeholder complete."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))