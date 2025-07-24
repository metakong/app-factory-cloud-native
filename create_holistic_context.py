import os
from datetime import datetime
from google.cloud import secretmanager_v1
from google.cloud import storage
from google.cloud import run_v2
from google.api_core import exceptions

def get_gcp_context(project_id: str) -> str:
    """
    Fetches and formats information about key GCP resources for the holistic context file.
    """
    context_parts = []
    
    # --- 1. Fetch Secrets ---
    try:
        secrets_output = "--- GCP Secret Manager Secrets ---\n\n"
        secrets_client = secretmanager_v1.SecretManagerServiceClient()
        parent = f"projects/{project_id}"
        secrets_output += "{:<60} {:<25} {:<25}\n".format("NAME", "LOCATION", "CREATED")
        secrets_output += "-" * 110 + "\n"
        for secret in secrets_client.list_secrets(request={"parent": parent}):
            secret_name = secret.name.split('/')[-1]
            # Location is derived from the replication policy
            location = "Automatically replicated"
            if secret.replication.user_managed:
                location = ",".join([r.location for r in secret.replication.user_managed.replicas])
            
            create_time = secret.create_time.strftime("%-m/%-d/%y, %-I:%M %p")
            secrets_output += "{:<60} {:<25} {:<25}\n".format(secret_name, location, create_time)
        context_parts.append(secrets_output)
    except exceptions.PermissionDenied as e:
        context_parts.append(f"--- GCP Secret Manager Secrets ---\n\nError: Permission denied. Ensure Secret Manager API is enabled and the user has 'secretmanager.secrets.list' permission.\nDetails: {e}\n")
    except Exception as e:
        context_parts.append(f"--- GCP Secret Manager Secrets ---\n\nError fetching secrets: {e}\n")

    # --- 2. Fetch GCS Buckets ---
    try:
        buckets_output = "\n--- GCP Storage Buckets ---\n\n"
        storage_client = storage.Client(project=project_id)
        buckets_output += "{:<40} {:<15} {:<15} {:<15}\n".format("NAME", "LOCATION", "PUBLIC ACCESS", "ACCESS CONTROL")
        buckets_output += "-" * 90 + "\n"
        for bucket in storage_client.list_buckets():
            public_access = "Not public" if bucket.iam_configuration.public_access_prevention == "enforced" else "Public"
            access_control = "Uniform" if bucket.iam_configuration.uniform_bucket_level_access_enabled else "Fine-grained"
            buckets_output += "{:<40} {:<15} {:<15} {:<15}\n".format(bucket.name, bucket.location, public_access, access_control)
        context_parts.append(buckets_output)
    except Exception as e:
        context_parts.append(f"\n--- GCP Storage Buckets ---\n\nError fetching buckets: {e}\n")

    # --- 3. Fetch Cloud Run Services ---
    try:
        run_output = "\n--- GCP Cloud Run Services ---\n\n"
        run_client = run_v2.ServicesClient()
        region = "us-central1" # Or loop through all supported regions
        parent = f"projects/{project_id}/locations/{region}"
        run_output += "{:<40} {:<15} {:<80}\n".format("NAME", "REGION", "URL")
        run_output += "-" * 135 + "\n"
        services_found = False
        for service in run_client.list_services(parent=parent):
            services_found = True
            service_name = service.name.split('/')[-1]
            run_output += "{:<40} {:<15} {:<80}\n".format(service_name, region, service.uri)
        if not services_found:
            run_output += "No Cloud Run services found in this region.\n"
        context_parts.append(run_output)
    except exceptions.PermissionDenied as e:
        context_parts.append(f"\n--- GCP Cloud Run Services ---\n\nError: Permission denied. Ensure Cloud Run Admin API is enabled and the user has 'run.services.list' permission.\nDetails: {e}\n")
    except Exception as e:
        context_parts.append(f"\n--- GCP Cloud Run Services ---\n\nError fetching Cloud Run services: {e}\n")
        
    return "\n".join(context_parts)

def get_local_file_context():
    """
    Reads all relevant local project files and concatenates them into a single string.
    """
    local_context = []
    files_to_include = [
        '.gitignore', 'README.md', 'api-spec.yaml', 'cloudbuild.yaml', 
        'deploy.sh', 'iam_setup.sh', 'most-recent-build-attempt-07202025-1929',
        'project_description.txt', 'substitutions.yaml',
        'backend/.env.example', 'backend/compose.yaml',
        'backend/shared/gcp_client.py', 'backend/shared/utils.py',
        'backend/services/discovery_cycle/Dockerfile', 'backend/services/discovery_cycle/main.py', 'backend/services/discovery_cycle/requirements.txt',
        'backend/services/cso_vetting/Dockerfile', 'backend/services/cso_vetting/main.py', 'backend/services/cso_vetting/requirements.txt',
        'backend/services/cpo_analysis/Dockerfile', 'backend/services/cpo_analysis/main.py', 'backend/services/cpo_analysis/requirements.txt',
        'backend/services/ai_developer/Dockerfile', 'backend/services/ai_developer/main.py', 'backend/services/ai_developer/requirements.txt',
        'backend/services/cmo_publishing/Dockerfile', 'backend/services/cmo_publishing/main.py', 'backend/services/cmo_publishing/requirements.txt',
        'backend/tools/robust_web_scraper/Dockerfile', 'backend/tools/robust_web_scraper/main.py', 'backend/tools/robust_web_scraper/requirements.txt',
        'backend/tools/google_play_publisher/Dockerfile', 'backend/tools/google_play_publisher/main.py', 'backend/tools/google_play_publisher/requirements.txt',
        'frontend/Dockerfile', 'frontend/index.html', 'frontend/script.js', 'frontend/style.css'
    ]
    
    for file_path in files_to_include:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                local_context.append(f"--- File: {file_path} ---\n\n{content}\n")
        except FileNotFoundError:
            local_context.append(f"--- File: {file_path} ---\n\n[File not found]\n")
        except Exception as e:
            local_context.append(f"--- File: {file_path} ---\n\n[Error reading file: {e}]\n")
            
    return "\n".join(local_context)

if __name__ == '__main__':
    gcp_project_id = os.environ.get("GCP_PROJECT", "app-factory-v2")
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"holistic_context-{timestamp}.txt"
    
    print(f"Generating context file: {filename}...")

    with open(filename, 'w') as f:
        f.write(f"Project Context for {gcp_project_id}\n")
        f.write(f"Generated on: {datetime.now().isoformat()}\n")
        f.write("================================================================================\n\n")
        
        # Fetch and write GCP context first
        gcp_context = get_gcp_context(gcp_project_id)
        f.write(gcp_context)
        f.write("\n================================================================================\n")
        
        # Fetch and write local file context
        local_context = get_local_file_context()
        f.write(local_context)
    
    print(f"Successfully created {filename}.")