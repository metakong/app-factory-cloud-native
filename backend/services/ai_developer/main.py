import os
import json
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, get_secret
import google.generativeai as genai
from github import Github, GithubException
from google.cloud import storage
from google.cloud.devtools import cloudbuild_v1

app = Flask(__name__)
logger = get_logger(__name__)

# --- Constants ---
METAKONG_GITHUB_USER = "metakong"
GITHUB_SECRET_NAME = "github-token"
GEMINI_SECRET_NAME = "gemini-api-key"
PROJECT_ID = os.environ.get("GCP_PROJECT", "app-factory-v2")
REGION = "us-central1"
APK_BUCKET_NAME = f"{PROJECT_ID}-apks"

# Initialize Google Cloud clients
build_client = cloudbuild_v1.CloudBuildClient()

@app.route("/")
def health_check():
    return "OK", 200

def generate_flutter_app_and_pipeline(spec: str, idea_id: str, feedback: str) -> dict:
    """
    Calls the Gemini API to generate a complete Flutter application codebase
    and a Cloud Build pipeline to build and sign a release APK.
    """
    logger.info(f"Generating full Flutter app and CI/CD pipeline for idea: {idea_id}")
    
    api_key = get_secret(GEMINI_SECRET_NAME)
    if not api_key:
        raise ValueError(f"Could not retrieve secret: {GEMINI_SECRET_NAME}")
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    Act as an expert Flutter developer and a DevOps engineer specializing in mobile CI/CD pipelines.
    Your task is to generate a complete, functional, multi-screen Flutter application based on the provided specification and CEO feedback.
    You must also generate a `cloudbuild.yaml` file to build a signed, release-ready .apk and upload it to Google Cloud Storage.

    **Directives**:
    1.  **Output Format**: Return the output as a single, valid JSON object. The keys must be the full file paths (e.g., `lib/main.dart`, `pubspec.yaml`, `cloudbuild.yaml`), and the values must be the complete string content for each file.
    2.  **Flutter Application**:
        - The application must be a functional, multi-screen app (e.g., a list view and a detail view).
        - The code must be clean, well-commented, and follow Flutter best practices.
        - Generate a `pubspec.yaml` with necessary dependencies (like http or provider).
        - Generate a `README.md` that briefly describes the application.
    3.  **CI/CD Pipeline (`cloudbuild.yaml`)**:
        - The pipeline must build a signed, release-ready Android APK.
        - It must have access to secrets from Secret Manager.
        - Step 1: Use a builder to download the signing keystore (`keystore.jks`) from Secret Manager (secret name: 'flutter-keystore-jks'). Place it in `android/app/keystore.jks`.
        - Step 2: Use a builder to download the key properties (`key.properties`) from Secret Manager (secret name: 'flutter-key-properties'). Place it in `android/key.properties`.
        - Step 3: Use a Flutter build environment (e.g., `cirrusci/flutter:stable`) to run `flutter pub get`.
        - Step 4: In the same Flutter environment, run `flutter build apk --release`. The build process will automatically use the `key.properties` and `keystore.jks` to sign the APK.
        - Step 5: Use the `gcr.io/cloud-builders/gsutil` builder to copy the final APK from `build/app/outputs/flutter-apk/app-release.apk` to the Cloud Storage bucket `gs://{APK_BUCKET_NAME}/{idea_id}/app-release.apk`.
        - Step 6: Use `gsutil` to make the uploaded APK publicly readable (`gsutil iam ch allUsers:objectViewer`).

    **Product Specification & SWOT**:
    ---
    {spec}
    ---

    **CEO Feedback**:
    ---
    {feedback}
    ---
    """
    
    response = model.generate_content(prompt)
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(cleaned_response)

def create_and_commit_to_github(token: str, repo_name: str, files: dict, description: str) -> str:
    """Creates a new GitHub repository and commits the generated files."""
    logger.info(f"Connecting to GitHub to create repository: {repo_name}")
    g = Github(token)
    user = g.get_user(METAKONG_GITHUB_USER)

    try:
        repo = user.create_repo(name=repo_name, description=description, private=False)
        logger.info(f"Successfully created public repository: {repo.full_name}")
    except GithubException as e:
        if e.status == 422 and "name already exists" in str(e.data):
            logger.warning(f"Repository '{repo_name}' already exists. Re-using.")
            repo = user.get_repo(repo_name)
        else:
            raise

    # Create a single commit with all files for efficiency
    master_ref = repo.get_git_ref('heads/main')
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    
    element_list = list()
    for filepath, content in files.items():
        element = cloudbuild_v1.GitSource(path=filepath, content=content, type='blob', mode='100644')
        element_list.append(element)

    tree = repo.create_git_tree(element_list, base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit("Initial commit of generated app source", tree, [parent])
    master_ref.edit(commit.sha)
    
    logger.info(f"Committed all files to {repo.full_name}")
    return repo.html_url

def trigger_cloud_build(repo_name: str, idea_id: str):
    """Creates and runs a Cloud Build trigger for the new repository."""
    logger.info(f"Triggering Cloud Build for repository: {repo_name}")
    
    build = cloudbuild_v1.Build()
    build.source = {
        "repo_source": {
            "project_id": PROJECT_ID,
            "repo_name": repo_name,
            "branch_name": "main"
        }
    }
    build.timeout = {"seconds": 3600} # 1 hour timeout for the build
    
    operation = build_client.create_build(project_id=PROJECT_ID, build=build)
    logger.info(f"Started build operation: {operation.metadata.build.id}")
    return operation

@app.route('/develop', methods=['POST'])
def develop_app():
    data = request.get_json()
    idea_id = data.get("idea_id")
    ceo_feedback = data.get("feedback", "No specific feedback provided.")
    
    if not idea_id:
        return jsonify({"status": "error", "message": "Missing 'idea_id'."}), 400

    logger.info(f"AI Developer Agent received request for idea: {idea_id}")

    try:
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea or "product_spec_and_swot" not in app_idea:
            raise ValueError("Product specification not found in Firestore document.")
        
        generated_files = generate_flutter_app_and_pipeline(
            spec=app_idea["product_spec_and_swot"],
            idea_id=idea_id,
            feedback=ceo_feedback
        )

        github_token = get_secret(GITHUB_SECRET_NAME)
        if not github_token:
            raise ValueError(f"Could not retrieve secret: {GITHUB_SECRET_NAME}")
        
        repo_name = f"app-factory-{idea_id}"
        repo_url = create_and_commit_to_github(
            token=github_token,
            repo_name=repo_name,
            files=generated_files,
            description=app_idea.get("description", "An AI-generated mobile application.")
        )
        
        # This is the new, critical step to start the build
        trigger_cloud_build(repo_name, idea_id)
        
        apk_download_url = f"https://storage.googleapis.com/{APK_BUCKET_NAME}/{idea_id}/app-release.apk"

        update_data = {
            "status": "PENDING_CEO_TESTING",
            "repo_url": repo_url,
            "apk_download_url": apk_download_url
        }
        save_to_firestore("app_ideas", idea_id, update_data)
        
        logger.info(f"Successfully developed, committed, and triggered build for '{idea_id}'.")
        return jsonify({"status": "success", "message": f"Development and build started for {idea_id}.", "repo_url": repo_url}), 200

    except Exception as e:
        logger.error(f"Development failed for '{idea_id}': {e}")
        save_to_firestore("app_ideas", idea_id, {"status": "DEVELOPMENT_FAILED", "error": str(e)})
        return jsonify({"status": "error", "message": f"Development failed: {e}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))