import argparse
import sys
import os
import time

try:
    from .utils import normalize_url
    from .checker import check_robots, check_ucp_config, check_homepage
    from .scorer import calculate_score
    from .reporter import generate_report, generate_pdf
    from .logger import logger
except ImportError:
    from utils import normalize_url
    from checker import check_robots, check_ucp_config, check_homepage
    from scorer import calculate_score
    from reporter import generate_report, generate_pdf
    from logger import logger

def main() -> None:
    parser = argparse.ArgumentParser(description="UCP Compliance Scanner")
    parser.add_argument("url", help="The website URL to check")
    parser.add_argument("--output", "-o", help="Specific output filename (optional)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON result to stdout instead of generating reports")
    
    args = parser.parse_args()
    
    try:
        raw_url, base_url, host, tld, is_us_guess = normalize_url(args.url)
    except Exception as e:
        logger.error(f"Failed to normalize URL {args.url}: {e}")
        sys.exit(1)
    
    if not base_url:
        logger.error(f"Invalid URL provided: {args.url}")
        sys.exit(1)
        
    logger.info(f"Scanning {base_url}...")
    
    # Perform checks
    logger.info("Checking robots.txt...")
    robots_res = check_robots(base_url)
    
    logger.info("Checking UCP config...")
    ucp_res = check_ucp_config(base_url)
    
    logger.info("Checking homepage headers...")
    home_res = check_homepage(base_url)
    
    logger.info("Calculating score...")
    result = calculate_score(base_url, host, is_us_guess, robots_res, ucp_res, home_res)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2, default=str))
    else:
        logger.info("Generating reports...")
        
        # Create output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        sanitized_host = host.replace('.', '_')
        timestamp = int(time.time())
        filename_base = f"UCP_Report_{sanitized_host}_{timestamp}"
        
        # Determine file paths
        if args.output:
            output_html = args.output
            if output_html.endswith('.html'):
                output_pdf = output_html.replace('.html', '.pdf')
            else:
                output_pdf = output_html + '.pdf'
                output_html = output_html + '.html'
        else:
            output_html = os.path.join(output_dir, f"{filename_base}.html")
            output_pdf = os.path.join(output_dir, f"{filename_base}.pdf")
        
        # Generate HTML
        try:
            html_content = generate_report(result)
            with open(output_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML Report generated: {os.path.abspath(output_html)}")
        except Exception as e:
            logger.error(f"Failed to write HTML report: {e}")
            sys.exit(1)
        
        # Generate PDF
        try:
            generate_pdf(output_html, output_pdf)
            logger.info(f"PDF Report generated: {os.path.abspath(output_pdf)}")
        except ImportError:
            logger.warning("Playwright not installed or configured. PDF generation skipped.")
            logger.warning("Run: uv add playwright && uv run playwright install chromium")
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            # Do not exit error, as HTML was successful

if __name__ == "__main__":
    main()
