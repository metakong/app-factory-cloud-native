import os
import datetime
import subprocess

# --- Configuration ---
OUTPUT_FILENAME_TEMPLATE = "holistic_context-{date}-{time}.txt"
# Directories to completely ignore.
DIRECTORIES_TO_IGNORE = {
    ".git", ".vscode", ".idea", "__pycache__", "env", "venv", ".venv", "node_modules",
}
# Specific files to ignore.
FILES_TO_IGNORE = {
    ".DS_Store", "tfplan", ".terraform.lock.hcl", "create_context_file.py", "create_holistic_context.py"
}
# --- End Configuration ---

def should_ignore(path: str, is_dir: bool) -> bool:
    """Checks if a given file or directory should be ignored."""
    basename = os.path.basename(path)
    if is_dir:
        return basename in DIRECTORIES_TO_IGNORE
    return basename in FILES_TO_IGNORE

def get_latest_cloud_build_log() -> str:
    """Fetches the log for the most recent Google Cloud Build."""
    print("\nFetching latest Google Cloud Build log...")
    try:
        # Command to get the ID of the most recent build
        get_id_command = "gcloud builds list --limit=1 --format='value(id)'"
        build_id = subprocess.check_output(get_id_command, shell=True, text=True, stderr=subprocess.PIPE).strip()

        if not build_id:
            print("  ! No build ID found.")
            return "No Google Cloud Build logs found or gcloud CLI is not configured.\n"

        print(f"  + Found latest build ID: {build_id}")

        # Command to get the log for that build ID
        get_log_command = f"gcloud builds log {build_id}"
        log_content = subprocess.check_output(get_log_command, shell=True, text=True, stderr=subprocess.PIPE)
        print("  + Successfully fetched build log.")
        return log_content

    except subprocess.CalledProcessError as e:
        error_message = f"  ! Error fetching Cloud Build logs: {e.stderr}\n"
        print(error_message)
        return error_message
    except FileNotFoundError:
        error_message = "  ! 'gcloud' command not found. Is the Google Cloud SDK installed and in your PATH?\n"
        print(error_message)
        return error_message

def generate_context_file():
    """Walks the project directory and writes file contents and logs to a single output file."""
    project_root = os.getcwd()
    now = datetime.datetime.now()
    output_filename = now.strftime(OUTPUT_FILENAME_TEMPLATE.format(date="%Y%m%d", time="%H%M%S"))

    # Add the dynamic output filename to the ignore list for this run
    current_files_to_ignore = FILES_TO_IGNORE.union({output_filename})

    file_count = 0
    print(f"Starting context generation in root directory: {project_root}")

    with open(output_filename, "w", encoding="utf-8") as outfile:
        outfile.write(f"Project Context for app-factory-v2\n")
        outfile.write(f"Generated on: {now.isoformat()}\n")
        outfile.write("=" * 80 + "\n\n")

        # --- Append Cloud Build Log ---
        outfile.write("--- Google Cloud Build Log (Latest) ---\n\n")
        log_data = get_latest_cloud_build_log()
        outfile.write(log_data)
        outfile.write("\n\n" + "=" * 80 + "\n\n")

        # --- Append File Contents ---
        print("\nWalking project directory to add file contents...")
        for root, dirs, files in os.walk(project_root, topdown=True):
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), True)]

            for filename in sorted(files):
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, project_root)

                if os.path.basename(relative_path) in current_files_to_ignore:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors='strict') as infile:
                        content = infile.read()
                    outfile.write(f"--- File: {relative_path} ---\n\n")
                    outfile.write(content)
                    outfile.write("\n\n" + "=" * 80 + "\n\n")
                    file_count += 1
                    print(f"  + Added: {relative_path}")
                except UnicodeDecodeError:
                    print(f"  ! Skipped (binary file): {relative_path}")
                except Exception as e:
                    print(f"  ! Error reading {relative_path}: {e}")

    print(f"\nContext generation complete.")
    print(f"Added {file_count} files and the latest build log to '{output_filename}'.")

if __name__ == "__main__":
    generate_context_file()