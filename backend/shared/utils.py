import logging
import google.cloud.logging

def get_logger(name: str) -> logging.Logger:
    """Configures a logger for structured JSON logs."""
    client = google.cloud.logging.Client()
    handler = client.get_default_handler()
    logger = logging.getLogger(name)
    if not any(isinstance(h, type(handler)) for h in logger.handlers):
        logger.addHandler(handler)
    logger.setLevel(logging.INFO) [cite: 2328]
    return logger [cite: 94]