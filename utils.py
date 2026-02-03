from urllib.parse import urlparse

def normalize_url(raw_url):
    raw = str(raw_url).strip()
    if not raw:
        return None, None, None, None, None

    if not raw.startswith(('http://', 'https://')):
        url_with_scheme = f'https://{raw}'
    else:
        url_with_scheme = raw

    try:
        parsed = urlparse(url_with_scheme)
        host = parsed.hostname
        parts = host.split('.')
        tld = parts[-1] if parts else 'com'
        is_us_guess = tld == 'us'
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        return raw, base_url, host, tld, is_us_guess
    except Exception:
        # Fallback similar to n8n logic, though mostly urlparse will handle or raise
        return raw, 'https://example.com', 'example.com', 'com', False
