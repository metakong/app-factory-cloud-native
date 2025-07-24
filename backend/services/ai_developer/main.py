import os
import json
import traceback
from flask import Flask, request, jsonify
from shared.utils import get_logger
from shared.gcp_client import get_from_firestore, save_to_firestore, get_secret
import google.generativeai as genai
from github import Github, GithubException, InputGitTreeElement
from google.cloud import storage
from google.cloud.devtools import cloudbuild_v1

app = Flask(__name__)
logger = get_logger(__name__)

# --- Constants & Configuration ---
METAKONG_GITHUB_USER = "metakong"
GITHUB_SECRET_NAME = "github-token"
GEMINI_SECRET_NAME = "gemini-api-key"
PROJECT_ID = os.environ.get("GCP_PROJECT", "app-factory-v2")
REGION = "us-central1"
APK_BUCKET_NAME = f"{PROJECT_ID}-apks"

# --- GCP Client Initialization ---
try:
    build_client = cloudbuild_v1.CloudBuildClient()
    storage_client = storage.Client()
except Exception as e:
    logger.critical(f"Failed to initialize GCP clients: {e}")
    # The application will not be able to function without these clients.
    # In a real production scenario, this might trigger a graceful shutdown or health check failure.

# --- Internal CI/CD Template for Generated Apps ---
# This template is more reliable than asking an LLM to generate a complex YAML file.
# It will be populated with the specific idea_id and bucket name.
GENERATED_APP_CLOUDBUILD_TEMPLATE = """
steps:
# 1. Access Keystore from Secret Manager
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      gcloud secrets versions access latest --secret="flutter-keystore-jks" --project="${PROJECT_ID}" --format='get(payload.data)' | tr '_-' '/+' | base64 -d > android/app/keystore.jks
  id: 'Get Keystore'

# 2. Access Key Properties from Secret Manager
- name: 'gcr.io/cloud-builders/gcloud'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      gcloud secrets versions access latest --secret="flutter-key-properties" --project="${PROJECT_ID}" > android/key.properties
  id: 'Get Key Properties'

# 3. Setup Flutter and Build APK
- name: 'cirrusci/flutter:stable'
  args: ['flutter', 'build', 'apk', '--release']
  id: 'Build Release APK'
  waitFor: ['Get Keystore', 'Get Key Properties']

# 4. Upload APK to Cloud Storage
- name: 'gcr.io/cloud-builders/gsutil'
  args:
    - 'cp'
    - 'build/app/outputs/flutter-apk/app-release.apk'
    - 'gs://{apk_bucket_name}/{idea_id}/app-release.apk'
  id: 'Upload APK'
  waitFor: ['Build Release APK']

# 5. Make APK public for CEO review
- name: 'gcr.io/cloud-builders/gsutil'
  args: ['iam', 'ch', 'allUsers:objectViewer', 'gs://{apk_bucket_name}/{idea_id}/app-release.apk']
  id: 'Make APK Public'
  waitFor: ['Upload APK']

# 6. Notify App Factory of Build Completion
- name: 'gcr.io/cloud-builders/curl'
  entrypoint: 'bash'
  args:
    - '-c'
    - |
      set -e
      ACCESS_TOKEN=$(gcloud auth print-identity-token --audiences="{developer_service_url}")
      curl -X POST "{developer_service_url}/build-complete" -H "Authorization: Bearer $$ACCESS_TOKEN" -H "Content-Type: application/json" -d '{ "idea_id": "{idea_id}", "build_status": "SUCCESS" }'
  id: 'Notify Success'
  waitFor: ['Make APK Public']

options:
  logging: CLOUD_LOGGING_ONLY
  # Higher machine type might be needed for complex Flutter builds
  machineType: 'E2_HIGHCPU_8'
"""

@app.route("/")
def health_check():
    """Provides a simple health check endpoint for monitoring."""
    return "OK", 200

def generate_flutter_app_code(spec: dict, feedback: str) -> dict:
    """Calls the Gemini API to generate the Flutter application codebase."""
    logger.info("Generating Flutter application source code using Gemini.")
    
    api_key = get_secret(GEMINI_SECRET_NAME)
    if not api_key:
        raise ValueError(f"Could not retrieve secret: {GEMINI_SECRET_NAME}")
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert Flutter developer. Your task is to generate a complete, functional, multi-screen Flutter application based on the provided product brief and CEO feedback.

    **Directives**:
    1.  **Output Format**: Return the output as a single, valid JSON object. The keys must be the full file paths (e.g., `lib/main.dart`, `pubspec.yaml`), and the values must be the complete string content for each file. Do not wrap the JSON in markdown backticks.
    2.  **Application Quality**: The code must be clean, well-commented, null-safe, and follow modern Flutter best practices (e.g., use of `provider` or `riverpod` for state management).
    3.  **Core Files**: You MUST generate at least the following files:
        - `pubspec.yaml`: Include necessary dependencies.
        - `lib/main.dart`: The main entry point of the app.
        - At least two separate screen/widget files in the `lib/` directory (e.g., `lib/home_screen.dart`, `lib/detail_screen.dart`).
        - `README.md`: A brief description of the application.

    **Product Brief**:
    - App Title: {spec.get('ai_title')}
    - App Summary: {spec.get('ai_summary')}

    **CEO Feedback**:
    ---
    {feedback}
    ---
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean up potential markdown formatting from the LLM response
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)
    except Exception as e:
        logger.error(f"Error generating or parsing Gemini response: {e}")
        raise

def create_and_commit_to_github(token: str, repo_name: str, files: dict, description: str) -> str:
    """Creates a new GitHub repository and commits the generated files."""
    logger.info(f"Connecting to GitHub to create repository: {repo_name}")
    g = Github(token)
    user = g.get_user(METAKONG_GITHUB_USER)

    try:
        repo = user.create_repo(name=repo_name, description=description, private=False)
        logger.info(f"Successfully created public repository: {repo.full_name}")
    except GithubException as e:
        if e.status == 422 and "name already exists" in str(e.data.get("message", "")):
            logger.warning(f"Repository '{repo_name}' already exists. Re-using.")
            repo = user.get_repo(repo_name)
        else:
            logger.error(f"GitHub API error: {e.data}")
            raise

    # Create file blobs and tree for a single commit
    tree_elements = [
        InputGitTreeElement(path=filepath, mode='100644', type='blob', content=content)
        for filepath, content in files.items()
    ]

    # Handle empty vs. existing repo
    try:
        main_ref = repo.get_git_ref('heads/main')
        latest_commit_sha = main_ref.object.sha
        base_tree = repo.get_git_tree(latest_commit_sha)
        parents = [repo.get_git_commit(latest_commit_sha)]
    except GithubException: # Main branch doesn't exist (empty repo)
        base_tree = None
        parents = []

    tree = repo.create_git_tree(tree_elements, base_tree)
    commit = repo.create_git_commit("feat: Initial application source generation", tree, parents)
    
    if parents: # Update existing main branch
        main_ref.edit(commit.sha)
    else: # Create new main branch
        repo.create_git_ref(ref='refs/heads/main', sha=commit.sha)
    
    logger.info(f"Committed all generated files to {repo.full_name}")
    return repo.html_url

def create_and_run_build_trigger(repo_name: str):
    """Creates and runs a Cloud Build trigger for the new repository."""
    logger.info(f"Creating and running Cloud Build trigger for repository: {repo_name}")

    trigger = cloudbuild_v1.BuildTrigger()
    trigger.name = f"{repo_name}-trigger"
    trigger.description = f"Build trigger for the {repo_name} application"
    trigger.github = cloudbuild_v1.GitHubEventsConfig(
        owner=METAKONG_GITHUB_USER,
        name=repo_name,
        push=cloudbuild_v1.PushFilter(branch="^main$"),
    )
    trigger.filename = "cloudbuild.yaml"

    try:
        created_trigger = build_client.create_build_trigger(
            project_id=PROJECT_ID, trigger=trigger
        )
        logger.info(f"Successfully created trigger: {created_trigger.id}")

        run_request = cloudbuild_v1.RunBuildTriggerRequest(
            project_id=PROJECT_ID,
            trigger_id=created_trigger.id,
            source=cloudbuild_v1.RepoSource(
                project_id=PROJECT_ID,
                repo_name=repo_name,
                branch_name="main"
            ),
        )
        operation = build_client.run_build_trigger(request=run_request)
        logger.info(f"Successfully started initial build operation: {operation.metadata.build.id}")
        return operation.metadata.build.id
    except Exception as e:
        logger.error(f"Failed to create or run build trigger for {repo_name}: {e}")
        raise

@app.route('/kickoff-development', methods=['POST'])
def kickoff_development():
    """
    Receives an app idea, generates code, commits to GitHub, and triggers a build.
    """
    data = request.get_json()
    idea_id = data.get("idea_id")
    product_brief = data.get("product_brief")

    if not all([idea_id, product_brief, product_brief.get("ai_title")]):
        logger.error("Invalid request payload received.")
        return jsonify({"status": "error", "message": "Invalid payload. 'idea_id' and 'product_brief' with 'ai_title' are required."}), 400

    logger.info(f"AI Developer Agent received kickoff request for idea: {idea_id}")
    
    try:
        app_idea = get_from_firestore("app_ideas", idea_id)
        if not app_idea:
            return jsonify({"status": "error", "message": f"Idea '{idea_id}' not found."}), 404
        if app_idea.get("status") != "PENDING_CEO_APPROVAL":
             return jsonify({"status": "error", "message": f"Idea '{idea_id}' is not in PENDING_CEO_APPROVAL state."}), 409

        # 1. Generate Flutter Code
        generated_code = generate_flutter_app_code(
            spec=product_brief,
            feedback=app_idea.get("ceo_feedback", "No specific feedback provided.")
        )

        # 2. Generate CI/CD Pipeline from Template
        developer_service_url = os.environ.get('K_SERVICE', '')
        if not developer_service_url:
             raise RuntimeError("K_SERVICE environment variable not found. Cannot set build callback URL.")

        generated_code['cloudbuild.yaml'] = GENERATED_APP_CLOUDBUILD_TEMPLATE.format(
            apk_bucket_name=APK_BUCKET_NAME,
            idea_id=idea_id,
            developer_service_url=developer_service_url
        )
        
        # 3. Commit to GitHub
        github_token = get_secret(GITHUB_SECRET_NAME)
        repo_name = f"app-factory-{idea_id.lower().replace('_', '-')}"
        repo_url = create_and_commit_to_github(
            token=github_token,
            repo_name=repo_name,
            files=generated_code,
            description=product_brief.get("ai_summary", "An AI-generated mobile application.")
        )
        
        # 4. Trigger Cloud Build
        build_id = create_and_run_build_trigger(repo_name)

        # 5. Update State to PENDING_BUILD
        update_data = {
            "status": "PENDING_BUILD",
            "repo_url": repo_url,
            "build_id": build_id,
            "error": firestore.DELETE_FIELD # Clear any previous errors
        }
        save_to_firestore("app_ideas", idea_id, update_data)
        
        logger.info(f"Successfully kicked off development for '{idea_id}'. Repo: {repo_url}")
        return jsonify({
            "status": "success",
            "message": f"Development pipeline initiated for {idea_id}.",
            "repo_url": repo_url
        }), 200

    except Exception as e:
        error_str = str(e)
        logger.exception(f"Development kickoff failed for '{idea_id}'. Stacktrace: {traceback.format_exc()}")
        save_to_firestore("app_ideas", idea_id, {"status": "DEVELOPMENT_FAILED", "error": error_str})
        return jsonify({"status": "error", "message": f"Development kickoff failed: {error_str}"}), 500

@app.route('/build-complete', methods=['POST'])
def build_complete():
    """Callback endpoint for the generated app's Cloud Build pipeline."""
    data = request.get_json()
    idea_id = data.get("idea_id")
    build_status = data.get("build_status")

    if not all([idea_id, build_status]):
        logger.error("Invalid build-complete callback payload.")
        return jsonify({"status": "error", "message": "Invalid payload. 'idea_id' and 'build_status' are required."}), 400

    logger.info(f"Received build completion notification for idea '{idea_id}' with status '{build_status}'.")

    try:
        if build_status == "SUCCESS":
            apk_url = f"https://storage.googleapis.com/{APK_BUCKET_NAME}/{idea_id}/app-release.apk"
            update_data = {
                "status": "PENDING_CEO_TESTING",
                "apk_download_url": apk_url
            }
            message = f"Build for {idea_id} succeeded. APK is ready for testing."
        else: # FAILURE
            update_data = {
                "status": "BUILD_FAILED",
                "error": "The Cloud Build pipeline for the generated application failed."
            }
            message = f"Build for {idea_id} failed."

        save_to_firestore("app_ideas", idea_id, update_data)
        logger.info(message)
        return jsonify({"status": "success", "message": message}), 200

    except Exception as e:
        logger.exception(f"Failed to process build-complete callback for '{idea_id}'. Stacktrace: {traceback.format_exc()}")
        # Don't update Firestore here as it might be in a bad state
        return jsonify({"status": "error", "message": "Failed to update Firestore status."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))