import requests
from typing import Dict, Any, Optional
try:
    from .logger import logger
except ImportError:
    from logger import logger

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def make_request(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Perform an HTTP GET request and return a standardized response dict.
    """
    try:
        logger.debug(f"Requesting URL: {url}")
        with requests.Session() as session:
            response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
            
        return {
            "statusCode": response.status_code,
            "body": response.text,
            "headers": dict(response.headers),
            "error": None
        }
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request failed for {url}: {e}")
        return {
            "statusCode": 0,
            "body": "",
            "headers": {},
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}", exc_info=True)
        return {
            "statusCode": 0,
            "body": "",
            "headers": {},
            "error": str(e)
        }

def check_robots(base_url: str) -> Dict[str, Any]:
    """Check availability and content of robots.txt."""
    url = f"{base_url}/robots.txt"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/plain, */*"
    }
    return make_request(url, headers)

def check_ucp_config(base_url: str) -> Dict[str, Any]:
    """Check availability and content of /.well-known/ucp."""
    url = f"{base_url}/.well-known/ucp"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, */*"
    }
    return make_request(url, headers)

def check_homepage(base_url: str) -> Dict[str, Any]:
    """Check homepage availability and headers."""
    url = base_url
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    return make_request(url, headers)
