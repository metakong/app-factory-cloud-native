import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

def get_resilient_session() -> requests.Session:
    """
    Returns a requests.Session object configured with a robust retry strategy
    that includes exponential backoff. This is crucial for resilient
    [cite_start]service-to-service communication. [cite: 99]
    """
    retry_strategy = Retry(
        total=3,  # Total number of retries
        status_forcelist=[429, 500, 502, 503, 504], # Status codes to retry on
        backoff_factor=1, # A delay factor of 1 means: 0.5s, 1s, 2s
        respect_retry_after_header=True
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    [cite_start]return session # [cite: 100]