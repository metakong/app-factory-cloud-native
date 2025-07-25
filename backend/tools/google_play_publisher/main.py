import os
import json
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, get_secret
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = get_logger(__name__)

# --- Configuration from Environment Variables ---
APK_BUCKET_NAME = os.environ.get("APK_BUCKET_NAME")

def get_play_service():
    """Authenticates and builds the Google Play Developer API service client."""
    try:
        creds_json_str = get_secret("google-play-api-key")
        if not creds_json_str:
            raise ValueError("Google Play API key secret not found.")
            
        creds_info = json.loads(creds_json_str)
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/androidpublisher']
        )
        return build('androidpublisher', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to authenticate with Google Play API: {e}")
        raise

def main():
    """Main function for the Google Play Publisher Cloud Run Job."""
    logger.info("Google Play Publisher Tool job started.")
    
    idea_id = os.environ.get("IDEA_ID")
    if not idea_id:
        logger.error("IDEA_ID environment variable not set. Exiting.")
        return

    if not APK_BUCKET_NAME:
        logger.error("APK_BUCKET_NAME environment variable not set. Exiting.")
        return
        
    try:
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            logger.error(f"App idea '{idea_id}' not found.")
            return

        package_name = f"com.appfactory.{idea_id.replace('-', '').lower()}"
        apk_gcs_path = f"{idea_id}/app-release.apk"
        local_apk_path = "/tmp/app-release.apk"

        logger.info(f"Downloading APK from gs://{APK_BUCKET_NAME}/{apk_gcs_path}")
        storage_client = storage.Client()
        bucket = storage_client.bucket(APK_BUCKET_NAME)
        blob = bucket.blob(apk_gcs_path)
        blob.download_to_filename(local_apk_path)
        logger.info(f"Successfully downloaded APK to {local_apk_path}")

        service = get_play_service()

        logger.info(f"Creating new edit for package: {package_name}")
        app_edit = service.edits().insert(packageName=package_name).execute()
        edit_id = app_edit['id']

        logger.info(f"Uploading APK for edit ID: {edit_id}")
        media = MediaFileUpload(local_apk_path, mimetype='application/vnd.android.package-archive')
        apk_upload_result = service.edits().apks().upload(
            packageName=package_name,
            editId=edit_id,
            media_body=media
        ).execute()
        version_code = apk_upload_result['versionCode']
        logger.info(f"Successfully uploaded APK with version code: {version_code}")

        logger.info("Assigning APK to the internal testing track.")
        service.edits().tracks().update(
            packageName=package_name,
            editId=edit_id,
            track='internal',
            body={'releases': [{'versionCodes': [str(version_code)], 'status': 'completed'}]}
        ).execute()

        logger.info(f"Committing edit ID: {edit_id}")
        service.edits().commit(packageName=package_name, editId=edit_id).execute()
        
        save_to_firestore("app_ideas", idea_id, {"status": "PUBLISHED"})
        logger.info(f"Successfully published app '{idea_id}' to the internal track.")

    except Exception as e:
        logger.exception(f"An error occurred during the publishing job for '{idea_id}'.")
        save_to_firestore("app_ideas", idea_id, {"status": "PUBLISHING_FAILED", "error": str(e)})
           
    logger.info("Google Play Publisher Tool job finished.")

if __name__ == "__main__":
    main()