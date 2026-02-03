import json
from datetime import datetime
from typing import Dict, Any, List
try:
    from .config import REPORT_CONFIG
    from .logger import logger
except ImportError:
    from config import REPORT_CONFIG
    from logger import logger

def calculate_score(
    base_url: str,
    host: str,
    is_us_guess: bool,
    robots_res: Dict[str, Any],
    ucp_res: Dict[str, Any],
    home_res: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate the UCP compliance score based on check results.
    """
    logger.info(f"Calculating compliance score for {host}")
    cfg = REPORT_CONFIG
    w = cfg['scoring']['weights']
    thr = cfg['scoring']['thresholds']
    pen = cfg['scoring']['penalties']
    
    review_date = datetime.utcnow().isoformat()
    
    # --- Component 1: Robots.txt ---
    robots_score = 0
    robots_finding = ''
    robots_detail = ''
    robots_body = robots_res.get('body', '') or ''
    robots_status = robots_res.get('statusCode', 0)
    
    # Defensive programming against None
    if robots_body is None: robots_body = ""
    
    if robots_res.get('error') or not robots_body:
        robots_score = 0
        robots_finding = 'robots.txt unreachable or empty'
        robots_detail = f"Endpoint: {base_url}/robots.txt; Status: {robots_status or 'N/A'}"
    elif 'ucp' in robots_body.lower() or '.well-known/ucp' in robots_body.lower():
        robots_score = w['robots']
        robots_finding = 'UCP reference found in robots.txt'
        robots_detail = f"Endpoint: {base_url}/robots.txt; Status: {robots_status or 'N/A'}"
    else:
        robots_score = 0
        robots_finding = 'No UCP directive in robots.txt'
        robots_detail = f"Endpoint: {base_url}/robots.txt; Status: {robots_status or 'N/A'}"
        
    component_robots = {
        'key': 'robots',
        'component': 'Robots.txt UCP directive',
        'weight': f"{w['robots']}%",
        'score': robots_score,
        'maxScore': w['robots'],
        'status': 'pass' if robots_score > 0 else 'fail',
        'finding': robots_finding,
        'detail': f"{cfg['scoring']['componentsCopy']['robots']}. {robots_detail}"
    }

    # --- Component 2: /.well-known/ucp ---
    ucp_score = 0
    ucp_finding = ''
    ucp_detail = ''
    ucp_json_valid = False
    ucp_body = ucp_res.get('body', '') or ''
    ucp_status = ucp_res.get('statusCode', 0)

    # Defensive programming
    if ucp_body is None: ucp_body = ""

    if ucp_res.get('error') or ucp_status == 0:
        ucp_score = 0
        ucp_finding = 'UCP config unreachable (timeout or error)'
        ucp_detail = f"Endpoint: {base_url}/.well-known/ucp; Status: {ucp_status or 'N/A'}"
    elif ucp_status == 200:
        try:
            parsed = json.loads(ucp_body)
            ucp_json_valid = isinstance(parsed, dict)
        except Exception as e:
            logger.debug(f"JSON parsing failed for UCP config: {e}")
            ucp_json_valid = False
            
        if ucp_json_valid:
            ucp_score = w['ucpConfig']
            ucp_finding = 'UCP config found (valid JSON)'
        else:
            ucp_score = 0
            ucp_finding = 'UCP config found but invalid (JSON validation error)'
            
        ucp_detail = f"Endpoint: {base_url}/.well-known/ucp; Status: {ucp_status}; JSON: {'valid' if ucp_json_valid else 'invalid/unknown'}"
    else:
        ucp_score = 0
        ucp_finding = f"UCP config missing or blocked (HTTP {ucp_status})"
        ucp_detail = f"Endpoint: {base_url}/.well-known/ucp; Status: {ucp_status}"
        
    component_ucp = {
        'key': 'ucpConfig',
        'component': 'UCP configuration file',
        'weight': f"{w['ucpConfig']}%",
        'score': ucp_score,
        'maxScore': w['ucpConfig'],
        'status': 'pass' if ucp_score > 0 else 'fail',
        'finding': ucp_finding,
        'detail': f"{cfg['scoring']['componentsCopy']['ucpConfig']}. {ucp_detail}"
    }

    # --- Component 3: HTTP Headers ---
    header_score = 0
    header_finding = ''
    header_detail = ''
    home_status = home_res.get('statusCode', 0)
    home_headers = home_res.get('headers', {}) or {}
    home_headers_text = json.dumps(home_headers).lower()

    if home_res.get('error') or home_status == 0:
        header_score = 0
        header_finding = 'Homepage unreachable (timeout or error)'
        header_detail = f"Endpoint: {base_url}; Status: {home_status or 'N/A'}"
    elif 200 <= home_status < 400:
        has_ucp_header = 'ucp' in home_headers_text or 'universal-content-protocol' in home_headers_text
        header_score = w['headers'] if has_ucp_header else 0
        header_finding = 'UCP-related headers detected' if has_ucp_header else 'No UCP-related headers detected'
        header_detail = f"Endpoint: {base_url}; Status: {home_status}"
    else:
        header_score = 0
        header_finding = f"Homepage returned unexpected status (HTTP {home_status})"
        header_detail = f"Endpoint: {base_url}; Status: {home_status}"
        
    component_headers = {
        'key': 'headers',
        'component': 'UCP HTTP headers',
        'weight': f"{w['headers']}%",
        'score': header_score,
        'maxScore': w['headers'],
        'status': 'pass' if header_score > 0 else 'fail',
        'finding': header_finding,
        'detail': f"{cfg['scoring']['componentsCopy']['headers']}. {header_detail}"
    }

    components = [component_robots, component_ucp, component_headers]
    weighted_average = max(0, min(100, round(robots_score + ucp_score + header_score)))

    status = 'NON_COMPLIANT'
    if weighted_average >= thr['compliantMin']:
        status = 'COMPLIANT'
    elif weighted_average >= thr['partialMin']:
        status = 'PARTIAL'
        
    cross_border = cfg['disclaimer']['crossBorderTemplateUS'] if is_us_guess else cfg['disclaimer']['crossBorderTemplateGeneric']
    
    return {
        'website': base_url, 
        'host': host,
        'reviewDate': review_date,
        'weightedAverage': weighted_average,
        'status': status,
        'components': components,
        'disclaimerComputed': {
            'reviewerLocation': cfg['disclaimer']['reviewerLocation'],
            'crossBorder': cross_border
        },
        'report': cfg 
    }
