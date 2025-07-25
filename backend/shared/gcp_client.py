import os
import google.auth.transport.requests
import google.oauth2.id_token
from google.cloud import firestore
from google.cloud import secretmanager
from .http_client import get_resilient_session # Import the new resilient session
from .utils import get_logger

# Initialize clients and logger
logger = get_logger(__name__)
project_id = os.environ.get("GCP_PROJECT", "app-factory-v2")
db = firestore.Client(project=project_id)
secret_client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_id: str, version_id: str = "latest") -> str:
    """Retrieves a secret value from Google Secret Manager."""
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    try:
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}")
        return ""

def save_to_firestore(collection: str, doc_id: str, data: dict):
    """Saves or updates a document in a Firestore collection."""
    try:
        doc_ref = db.collection(collection).document(doc_id)
        doc_ref.set(data, merge=True)
        logger.info(f"Successfully saved doc '{doc_id}' to collection '{collection}'.")
    except Exception as e:
        logger.error(f"Error saving to Firestore for doc '{doc_id}': {e}")
        raise

def get_from_firestore(collection: str, doc_id: str) -> dict | None:
    """Retrieves a document from a Firestore collection."""
    try:
        doc_ref = db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            logger.warning(f"Document '{doc_id}' not found in collection '{collection}'.")
            return None
    except Exception as e:
        logger.error(f"Error retrieving from Firestore for doc '{doc_id}': {e}")
        raise

def make_internal_request(service_url: str, method: str = 'GET', data: dict = None):
    """
    [cite_start]Makes an authenticated, resilient HTTP request to another internal Cloud Run service. [cite: 102]
    """
    try:
        # Fetch an OIDC token to authenticate the request
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, service_url)

        headers = {
            'Authorization': f'Bearer {id_token}',
            'Content-Type': 'application/json'
        }
        
        # [cite_start]Use the resilient session for the request [cite: 101]
        session = get_resilient_session()

        if method.upper() == 'POST':
            response = session.post(service_url, headers=headers, json=data, timeout=30)
        else:
            response = session.get(service_url, headers=headers, timeout=30)
        
        response.raise_for_status() # Raise an exception for bad status codes
        return response
        
    except Exception as e:
        logger.error(f"Error making internal request to {service_url}: {e}")
        raise