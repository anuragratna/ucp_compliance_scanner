import html
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from .logger import logger
except ImportError:
    from logger import logger

def generate_report(data: Dict[str, Any]) -> str:
    """Generate HTML Report String with Professional Design"""
    cfg = data.get('report', {})
    if not cfg:
        from config import REPORT_CONFIG
        cfg = REPORT_CONFIG
        
    t = cfg['ui']['theme']
    
    def esc(s: Any) -> str:
        return html.escape(str(s) if s is not None else '')

    def format_date(iso: str) -> str:
        try:
            dt = datetime.fromisoformat(iso)
            return dt.strftime("%B %d, %Y • %H:%M UTC")
        except Exception:
            return iso

    score = data.get('weightedAverage', 0)
    
    # Determine Status Colors and Icons
    if score >= cfg['scoring']['thresholds']['compliantMin']:
        status_color = "#10b981" # Emerald 500
        status_bg = "#ecfdf5"
        status_text = "COMPLIANT"
        status_icon = "shield-check"
    elif score >= cfg['scoring']['thresholds']['partialMin']:
        status_color = "#f59e0b" # Amber 500
        status_bg = "#fffbeb"
        status_text = "PARTIAL"
        status_icon = "alert-triangle"
    else:
        status_color = "#ef4444" # Red 500
        status_bg = "#fef2f2"
        status_text = "NON-COMPLIANT"
        status_icon = "shield-off"

    # SVG Gauge Generator
    def generate_gauge(value):
        # Semi-circle gauge (180 degrees)
        radius = 80
        circumference = 3.14159 * radius
        # value is 0-100, we Map to 0-circumference
        offset = circumference - (value / 100) * circumference
        
        return f"""
        <svg viewBox="0 0 200 110" class="gauge">
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#e5e7eb" stroke-width="20" stroke-linecap="round"/>
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="{status_color}" stroke-width="20" stroke-linecap="round" 
                  stroke-dasharray="{circumference}" stroke-dashoffset="{offset}" class="gauge-fill"/>
            <text x="100" y="85" text-anchor="middle" font-size="36" font-weight="bold" fill="#1f2937">{value}</text>
            <text x="100" y="105" text-anchor="middle" font-size="12" fill="#6b7280" font-weight="600">SCORE</text>
        </svg>
        """

    def recommendation_for(c: Dict[str, Any]) -> str:
        if c.get('status') == 'pass': return ''
        
        website = data.get('website', '')
        host = data.get('host', '')
        
        recs = {
            'robots': f"""<div class="recommendation">
              <div class="rec-title">⚡ ACTION REQUIRED</div>
              <p>Add the following UCP directive to <code>{esc(website)}/robots.txt</code>:</p>
              <div class="code-block">User-agent: *
Allow: /.well-known/ucp
UCP-Config: /.well-known/ucp</div>
            </div>""",
            'ucpConfig': f"""<div class="recommendation">
              <div class="rec-title">⚡ ACTION REQUIRED</div>
              <p>Deploy a valid JSON configuration at <code>{esc(website)}/.well-known/ucp</code>:</p>
              <div class="code-block">{{
  "version": "1.0",
  "publisher": "{esc(host)}",
  "contact": "admin@{esc(host)}",
  "ai_training": "opt-out"
}}</div>
            </div>""",
            'headers': f"""<div class="recommendation">
              <div class="rec-title">⚡ ACTION REQUIRED</div>
              <p>Configure your server to send these headers on the homepage:</p>
              <div class="code-block">UCP-Config: /.well-known/ucp
X-Robots-Tag: UCP-Enabled</div>
            </div>"""
        }
        return recs.get(c.get('key'), '')

    def component_row(c: Dict[str, Any]) -> str:
        status_pass = c.get('status') == 'pass'
        row_color = "#10b981" if status_pass else "#ef4444"
        icon = """<svg class="w-6 h-6 text-green-500" fill="none" stroke="#10b981" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>""" if status_pass else """<svg class="w-6 h-6 text-red-500" fill="none" stroke="#ef4444" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>"""
        
        return f"""
        <div class="component-card">
            <div class="card-header">
                <div class="card-title-group">
                    <div class="icon-box">
                        {icon}
                    </div>
                    <div>
                        <h3 class="card-title">{esc(c.get('component'))}</h3>
                        <div class="card-subtitle">{esc(c.get('finding'))}</div>
                    </div>
                </div>
                <div class="score-badge" style="background-color: {row_color}15; color: {row_color};">
                    {esc(c.get('score'))} / {esc(c.get('maxScore'))} pts
                </div>
            </div>
            <div class="card-body">
                <div class="detail-row">
                    <span class="detail-label">Endpoint Analysis:</span>
                    <span class="detail-value">{esc(c.get('detail'))}</span>
                </div>
                {recommendation_for(c)}
            </div>
        </div>"""

    components_html = "".join([component_row(c) for c in data.get('components', [])])
    
    privacy_paras_list = cfg['disclaimer']['paragraphs'] + [data.get('disclaimerComputed', {}).get('crossBorder', '')]
    privacy_html = "".join([f"<p class='disclaimer-text'>{esc(p)}</p>" for p in privacy_paras_list if p])

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        :root {{
            --primary: #2563eb;
            --text-main: #1f2937;
            --text-muted: #6b7280;
            --bg-body: #f3f4f6;
            --bg-card: #ffffff;
            --border: #e5e7eb;
        }}

        @page {{ margin: 0; size: A4; }}
        
        * {{ box-sizing: border-box; }}
        
        body {{ 
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            margin: 0;
            padding: 0;
            -webkit-print-color-adjust: exact;
        }}
        
        .container {{
            max-width: 210mm;
            margin: 0 auto;
            background: white;
            min-height: 297mm;
            padding: 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .header-hero {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: white;
            padding: 40px;
            position: relative;
            overflow: hidden;
        }}
        
        .header-bg-pattern {{
            position: absolute;
            top: 0; right: 0; bottom: 0; left: 0;
            opacity: 0.1;
            background-image: radial-gradient(#6366f1 1px, transparent 1px);
            background-size: 20px 20px;
        }}

        .report-header {{
            position: relative;
            z-index: 10;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}

        .brand-title h1 {{
            font-size: 28px;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.5px;
        }}
        
        .brand-title span {{ color: #60a5fa; }}
        .report-meta {{ font-size: 13px; color: #94a3b8; margin-top: 8px; }}

        .status-pill {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(4px);
            padding: 8px 16px;
            border-radius: 99px;
            font-weight: 600;
            font-size: 13px;
            border: 1px solid rgba(255,255,255,0.2);
            color: {status_color};
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .status-dot {{
            width: 8px; height: 8px;
            border-radius: 50%;
            background-color: {status_color};
            box-shadow: 0 0 8px {status_color};
        }}

        .content-body {{ padding: 40px; }}

        .executive-section {{
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 40px;
            margin-bottom: 40px;
            background: #fff;
            padding-bottom: 40px;
            border-bottom: 1px solid var(--border);
        }}

        .gauge-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        
        .gauge-fill {{
            transition: stroke-dashoffset 1s ease-out;
        }}

        .summary-text h2 {{
            font-size: 18px;
            font-weight: 700;
            margin: 0 0 12px 0;
            color: var(--text-main);
        }}
        
        .summary-desc {{
            font-size: 14px;
            color: var(--text-muted);
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }}
        
        .metric-item {{
            background: #f8fafc;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        
        .metric-label {{
            font-size: 11px;
            text-transform: uppercase;
            color: #64748b;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        
        .metric-value {{
            font-size: 14px;
            font-weight: 600;
            color: #0f172a;
        }}

        .section-title {{
            font-size: 16px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}

        .component-card {{
            background: white;
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }}

        .card-header {{
            padding: 16px 20px;
            background: #f8fafc;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .card-title-group {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .card-title {{
            font-size: 15px;
            font-weight: 700;
            margin: 0;
            color: #1e293b;
        }}
        
        .card-subtitle {{
            font-size: 13px;
            color: #64748b;
            margin-top: 2px;
        }}

        .score-badge {{
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
        }}

        .card-body {{ padding: 20px; }}
        
        .detail-row {{
            font-size: 13px;
            color: #334155;
            margin-bottom: 12px;
        }}
        
        .detail-label {{ font-weight: 600; color: #64748b; margin-right: 6px; }}

        .recommendation {{
            background: #ffffff;
            border: 1px solid #fbbf24;
            border-left-width: 4px;
            border-radius: 6px;
            padding: 16px;
            margin-top: 16px;
        }}
        
        .rec-title {{
            color: #d97706;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        
        .recommendation p {{
            font-size: 13px;
            margin: 0 0 8px 0;
            color: #4b5563;
        }}

        .code-block {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 12px;
            border-radius: 6px;
            font-family: 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
        }}

        .footer {{
            padding: 40px;
            background: #f8fafc;
            border-top: 1px solid var(--border);
            font-size: 12px;
            color: #94a3b8;
        }}
        
        .disclaimer-box {{
            margin-bottom: 20px;
        }}
        
        .disclaimer-title {{
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 8px;
            color: #64748b;
        }}
        
        .disclaimer-text {{
            margin-bottom: 6px;
            line-height: 1.5;
        }}
        
        .footer-meta {{
            border-top: 1px solid #e2e8f0;
            padding-top: 20px;
            display: flex;
            justify-content: space-between;
        }}
    </style>
    """
    
    html_content = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>UCP Compliance Report - {esc(data.get('host'))}</title>
  {css}
</head>
<body>
  <div class="container">
      <div class="header-hero">
          <div class="header-bg-pattern"></div>
          <div class="report-header">
              <div class="brand-title">
                  <h1>UCP <span>SCANNER</span></h1>
                  <div class="report-meta">Universal Content Protocol Assessment</div>
              </div>
              <div class="status-pill">
                  <div class="status-dot"></div>
                  {status_text}
              </div>
          </div>
      </div>
      
      <div class="content-body">
          <div class="executive-section">
              <div class="gauge-container">
                  {generate_gauge(score)}
              </div>
              <div class="summary-text">
                  <h2>Executive Summary</h2>
                  <p class="summary-desc">
                      This assessment evaluates <strong>{esc(data.get('host'))}</strong> against the Universal Content Protocol (UCP) standards. 
                      The site currently has a readiness score of <strong>{score}/100</strong>.
                  </p>
                  
                  <div class="metrics-grid">
                      <div class="metric-item">
                          <div class="metric-label">Review Date</div>
                          <div class="metric-value">{esc(format_date(data.get('reviewDate', '')))}</div>
                      </div>
                      <div class="metric-item">
                          <div class="metric-label">Target Host</div>
                          <div class="metric-value">{esc(data.get('host'))}</div>
                      </div>
                      <div class="metric-item">
                          <div class="metric-label">Protocol Ver</div>
                          <div class="metric-value">v1.0</div>
                      </div>
                  </div>
              </div>
          </div>

          <div class="component-section">
              <h3 class="section-title">Technical Breakdown</h3>
              {components_html}
          </div>
      </div>
      
      <div class="footer">
          <div class="disclaimer-box">
              <div class="disclaimer-title">{esc(cfg['disclaimer']['title'])}</div>
              {privacy_html}
          </div>
          <div class="footer-meta">
              <span>Generated by UCP Compliance Scanner v{esc(cfg['meta']['version'])}</span>
              <span>ID: {int(time.time())}</span>
          </div>
      </div>
  </div>
</body>
</html>"""
    return html_content

def generate_pdf(html_file_path: str, output_pdf_path: str) -> None:
    """Generate PDF from HTML string using Playwright."""
    logger.info(f"Generating PDF report at: {output_pdf_path}")
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Add args for better compatibility in some environments
            browser = p.chromium.launch(
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            
            # Convert file path to URI if not already
            if not html_file_path.startswith("file://"):
                file_uri = f"file://{os.path.abspath(html_file_path)}"
            else:
                file_uri = html_file_path
                
            page.goto(file_uri, wait_until="networkidle")
            
            # Add print styling
            page.add_style_tag(content="""
                @page { size: A4; margin: 0; }
                body { -webkit-print-color-adjust: exact; }
            """)
            
            page.pdf(
                path=output_pdf_path, 
                format="A4", 
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
            )
            browser.close()
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise
