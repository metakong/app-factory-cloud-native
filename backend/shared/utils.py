import logging
import sys
import google.cloud.logging

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a standardized logger that emits structured
    [cite_start]JSON logs compatible with Google Cloud Logging. [cite: 90, 91]
    """
    # The google-cloud-logging library automatically detects the GCP
    # environment and formats logs as structured JSON.
    client = google.cloud.logging.Client()
    handler = client.get_default_handler()

    # Get a logger for the specific module.
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers if the logger is requested multiple times.
    if not any(isinstance(h, type(handler)) for h in logger.handlers):
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    [cite_start]return logger # [cite: 94]