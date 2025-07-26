import os
import google.auth.transport.requests
import google.oauth2.id_token
from google.cloud import firestore, secretmanager
from .http_client import get_resilient_session
from .utils import get_logger

logger = get_logger(__name__)
project_id = os.environ.get("GCP_PROJECT", "app-factory-v2")
db = firestore.Client(project=project_id)
secret_client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_id: str, version_id: str = "latest") -> str:
    """Retrieves a secret from Google Secret Manager."""
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}" [cite: 2320]
    try:
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {e}")
        return ""

def save_to_firestore(collection: str, doc_id: str, data: dict):
    """Saves a document in Firestore."""
    try:
        doc_ref = db.collection(collection).document(doc_id)
        doc_ref.set(data, merge=True)
        logger.info(f"Successfully saved doc '{doc_id}' to collection '{collection}'.") [cite: 2321]
    except Exception as e:
        logger.error(f"Error saving to Firestore for doc '{doc_id}': {e}")
        raise

def get_from_firestore(collection: str, doc_id: str) -> dict | None:
    """Retrieves a document from Firestore."""
    try:
        doc_ref = db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        logger.error(f"Error retrieving from Firestore for doc '{doc_id}': {e}") [cite: 2323]
        raise

def make_internal_request(service_url: str, method: str = 'GET', data: dict = None):
    """Makes an authenticated request to an internal Cloud Run service."""
    try:
        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, service_url) [cite: 2324]
        headers = {'Authorization': f'Bearer {id_token}', 'Content-Type': 'application/json'}
        session = get_resilient_session()
        response = session.post(service_url, headers=headers, json=data, timeout=30) if method.upper() == 'POST' else session.get(service_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response
    except Exception as e:
        logger.error(f"Error making internal request to {service_url}: {e}")
        raise